import Foundation
import Combine
import ImageIO
import AVFoundation
import UniformTypeIdentifiers

enum MediaType {
    case image
    case video
    case unknown
}

enum RandomizationMode: String {
    case globalShuffle = "Global"
    case folderBalanced = "Folder-Balanced"
}

struct MediaItem: Identifiable, Equatable {
    let id = UUID()
    let url: URL
    let type: MediaType
    
    init(url: URL, type: MediaType) {
        self.url = url
        self.type = type
    }
    
    static func == (lhs: MediaItem, rhs: MediaItem) -> Bool {
        return lhs.url == rhs.url
    }
}

enum MediaManagerError: Error, LocalizedError, Equatable {
    case accessDenied
    case fileNotFound
    case scanFailed(String)
    case deleteFailed(String)
    case securityScopeAccessFailed
    
    var errorDescription: String? {
        switch self {
        case .accessDenied:
            return "Access to the folder was denied. Please check your permissions."
        case .fileNotFound:
            return "The file could not be found. It may have been moved or deleted."
        case .scanFailed(let reason):
            return "Failed to scan folder: \(reason)"
        case .deleteFailed(let reason):
            return "Failed to move to trash: \(reason)"
        case .securityScopeAccessFailed:
            return "Could not access the file due to security restrictions."
        }
    }
}

class MediaManager: ObservableObject {
    private static let randomizationModeDefaultsKey = "randomizationMode"
    
    @Published var mediaItems: [MediaItem] = []
    @Published var currentIndex: Int = -1
    @Published var isLoading: Bool = false
    @Published var currentSize: CGSize? = nil
    @Published var scanCount: Int = 0
    @Published var lastError: MediaManagerError? = nil
    @Published var randomizationMode: RandomizationMode = .globalShuffle {
        didSet {
            UserDefaults.standard.set(randomizationMode.rawValue, forKey: Self.randomizationModeDefaultsKey)
        }
    }
    
    private var isNavigating = false
    private let navigationDebounceInterval: TimeInterval = 0.1
    private var navigationDebounceTimer: Timer?
    private var currentScanWorkItem: DispatchWorkItem?
    private var currentScanURL: URL?
    private let scanLock = NSLock()
    
    init() {
        if let storedValue = UserDefaults.standard.string(forKey: Self.randomizationModeDefaultsKey),
           let storedMode = RandomizationMode(rawValue: storedValue) {
            randomizationMode = storedMode
        }
    }
    
    var currentItem: MediaItem? {
        guard currentIndex >= 0 && currentIndex < mediaItems.count else { return nil }
        return mediaItems[currentIndex]
    }
    
    func startScanning(at url: URL) {
        // Cancel any ongoing scan - thread-safe
        scanLock.lock()
        currentScanWorkItem?.cancel()
        currentScanWorkItem = nil
        scanLock.unlock()
        
        isLoading = true
        mediaItems = []
        currentIndex = -1
        scanCount = 0
        lastError = nil
        currentScanURL = url
        
        let didStartAccess = url.startAccessingSecurityScopedResource()
        
        guard didStartAccess else {
            DispatchQueue.main.async { [weak self] in
                self?.isLoading = false
                self?.lastError = .securityScopeAccessFailed
            }
            return
        }
        
        let workItem = DispatchWorkItem { [weak self] in
            defer {
                url.stopAccessingSecurityScopedResource()
            }
            
            guard let self = self else { return }
            
            let fileManager = FileManager.default
            let keys: [URLResourceKey] = [.isRegularFileKey, .contentTypeKey]
            
            guard let enumerator = fileManager.enumerator(at: url,
                                                        includingPropertiesForKeys: keys,
                                                        options: [.skipsHiddenFiles, .producesRelativePathURLs],
                                                        errorHandler: { (errorURL, error) -> Bool in
                print("Error at \(errorURL): \(error)")
                return true
            }) else {
                DispatchQueue.main.async { [weak self] in
                    self?.isLoading = false
                    self?.lastError = .scanFailed("Could not access folder contents")
                }
                return
            }
            
            var allItems: [MediaItem] = []
            var seenPaths = Set<String>() // Track seen paths to avoid duplicates
            
            for case let fileURL as URL in enumerator {
                // Check if scan was cancelled - thread-safe access
                self.scanLock.lock()
                let isCancelled = self.currentScanWorkItem?.isCancelled == true
                self.scanLock.unlock()
                
                if isCancelled {
                    break
                }
                
                autoreleasepool {
                    let fullURL = fileURL.absoluteURL.resolvingSymlinksInPath()
                    let pathExtension = fullURL.pathExtension.lowercased()
                    
                    var type: MediaType = .unknown
                    
                    // Use system's UTType to identify "image" or "audiovisual" content
                    // This supports HUNDREDS of file types natively (RAW, HEVC, ProRES, etc.)
                    if let utType = UTType(filenameExtension: pathExtension) {
                        if utType.conforms(to: .image) {
                            type = .image
                        } else if utType.conforms(to: .audiovisualContent) {
                            type = .video
                        }
                    } else {
                        // Fallback extensions for common types the system might not tag
                        let videoExts = ["mkv", "webm", "ogv", "3gp", "flv"]
                        if videoExts.contains(pathExtension) {
                            type = .video
                        }
                    }
                    
                    if type == .video && !self.isPlayableVideoFile(fullURL) {
                        return
                    }
                    
                    let canonicalPath = fullURL.path
                    if type != .unknown && !seenPaths.contains(canonicalPath) {
                        let newItem = MediaItem(url: fullURL, type: type)
                        allItems.append(newItem)
                        seenPaths.insert(canonicalPath)
                    }
                }
            }
            
            // Final step: Total Randomization and UI Update
            DispatchQueue.main.async { [weak self] in
                guard let self = self else { return }
                
                // Only update if this scan hasn't been cancelled
                // Use path comparison to handle symlinks and different URL representations
                // Normalize paths by removing trailing slashes for comparison
                let currentPath = self.currentScanURL?.path
                let scanPath = url.path
                let normalizedCurrent = currentPath?.hasSuffix("/") == true ? String(currentPath!.dropLast()) : currentPath
                let normalizedScan = scanPath.hasSuffix("/") ? String(scanPath.dropLast()) : scanPath
                
                // If scan was cancelled, reset loading state and return
                guard normalizedCurrent == normalizedScan else {
                    self.isLoading = false
                    return
                }
                
                self.mediaItems = self.buildPlaybackOrder(from: allItems)
                
                self.scanCount = self.mediaItems.count
                self.isLoading = false
                self.scanLock.lock()
                self.currentScanWorkItem = nil
                self.scanLock.unlock()
                
                if !self.mediaItems.isEmpty {
                    self.currentIndex = 0
                    self.updateCurrentSize()
                }
            }
        }
        
        scanLock.lock()
        currentScanWorkItem = workItem
        scanLock.unlock()
        DispatchQueue.global(qos: .userInitiated).async(execute: workItem)
    }
    
    func next() {
        guard !mediaItems.isEmpty && !isNavigating else { return }
        
        isNavigating = true
        
        // Invalidate any existing timer to prevent accumulation
        navigationDebounceTimer?.invalidate()
        
        if currentIndex < mediaItems.count - 1 {
            currentIndex += 1
        } else {
            // Rebuild order to keep it infinite and fresh according to selected randomization mode
            mediaItems = buildPlaybackOrder(from: mediaItems)
            currentIndex = 0
        }
        
        updateCurrentSize()
        
        // Reset navigation lock after debounce interval using Timer
        navigationDebounceTimer = Timer.scheduledTimer(withTimeInterval: navigationDebounceInterval, repeats: false) { [weak self] _ in
            self?.isNavigating = false
        }
    }
    
    func previous() {
        guard !mediaItems.isEmpty && !isNavigating else { return }
        
        isNavigating = true
        
        // Invalidate any existing timer to prevent accumulation
        navigationDebounceTimer?.invalidate()
        
        if currentIndex > 0 {
            currentIndex -= 1
        } else {
            currentIndex = mediaItems.count - 1
        }
        
        updateCurrentSize()
        
        // Reset navigation lock after debounce interval using Timer
        navigationDebounceTimer = Timer.scheduledTimer(withTimeInterval: navigationDebounceInterval, repeats: false) { [weak self] _ in
            self?.isNavigating = false
        }
    }
    
    func toggleRandomizationMode() {
        let current = randomizationMode
        randomizationMode = current == .globalShuffle ? .folderBalanced : .globalShuffle
        reorderItemsForCurrentMode()
    }
    
    private func reorderItemsForCurrentMode() {
        guard !mediaItems.isEmpty else { return }
        let currentItem = currentItem
        mediaItems = buildPlaybackOrder(from: mediaItems)
        if let currentItem,
           let newIndex = mediaItems.firstIndex(of: currentItem) {
            currentIndex = newIndex
        } else {
            currentIndex = 0
        }
        updateCurrentSize()
    }
    
    private func buildPlaybackOrder(from items: [MediaItem]) -> [MediaItem] {
        guard !items.isEmpty else { return [] }
        
        switch randomizationMode {
        case .globalShuffle:
            var shuffled = items
            shuffled.shuffle()
            return shuffled
        case .folderBalanced:
            var buckets: [String: [MediaItem]] = [:]
            for item in items {
                let folderPath = item.url.deletingLastPathComponent().path
                buckets[folderPath, default: []].append(item)
            }
            
            for key in buckets.keys {
                buckets[key]?.shuffle()
            }
            
            var ordered: [MediaItem] = []
            var activeFolders = Array(buckets.keys)
            activeFolders.shuffle()
            
            while !activeFolders.isEmpty {
                guard let selectedFolder = activeFolders.randomElement() else { break }
                guard var folderItems = buckets[selectedFolder], !folderItems.isEmpty else {
                    activeFolders.removeAll { $0 == selectedFolder }
                    continue
                }
                
                ordered.append(folderItems.removeFirst())
                
                if folderItems.isEmpty {
                    buckets[selectedFolder] = nil
                    activeFolders.removeAll { $0 == selectedFolder }
                } else {
                    buckets[selectedFolder] = folderItems
                }
            }
            
            return ordered
        }
    }
    
    private func isPlayableVideoFile(_ url: URL) -> Bool {
        let asset = AVURLAsset(url: url)
        let semaphore = DispatchSemaphore(value: 0)
        var isValid = false
        
        asset.loadValuesAsynchronously(forKeys: ["playable", "tracks"]) {
            defer { semaphore.signal() }
            
            var playableError: NSError?
            var tracksError: NSError?
            let playableStatus = asset.statusOfValue(forKey: "playable", error: &playableError)
            let tracksStatus = asset.statusOfValue(forKey: "tracks", error: &tracksError)
            
            guard playableStatus == .loaded, tracksStatus == .loaded else {
                return
            }
            
            guard asset.isPlayable else {
                return
            }
            
            let hasVideoTrack = !asset.tracks(withMediaType: .video).isEmpty
            isValid = hasVideoTrack
        }
        
        _ = semaphore.wait(timeout: .now() + 3.0)
        return isValid
    }
    
    private func updateCurrentSize() {
        guard let item = currentItem else { return }
        
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            var size: CGSize? = nil
            
            if item.type == .image {
                if let source = CGImageSourceCreateWithURL(item.url as CFURL, nil),
                   let properties = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [CFString: Any] {
                    let width = properties[kCGImagePropertyPixelWidth] as? CGFloat ?? 0
                    let height = properties[kCGImagePropertyPixelHeight] as? CGFloat ?? 0
                    
                    // Check orientation
                    let orientation = properties[kCGImagePropertyOrientation] as? Int ?? 1
                    if orientation >= 5 && orientation <= 8 {
                        size = CGSize(width: height, height: width)
                    } else {
                        size = CGSize(width: width, height: height)
                    }
                }
            } else if item.type == .video {
                let asset = AVAsset(url: item.url)
                
                // Use async loading to avoid blocking
                let semaphore = DispatchSemaphore(value: 0)
                var loadedSize: CGSize?
                
                asset.loadValuesAsynchronously(forKeys: ["tracks"]) {
                    defer { semaphore.signal() }
                    
                    var error: NSError?
                    let status = asset.statusOfValue(forKey: "tracks", error: &error)
                    
                    guard status == .loaded, 
                          let track = asset.tracks(withMediaType: .video).first else {
                        return
                    }
                    
                    let naturalSize = track.naturalSize
                    let transform = track.preferredTransform
                    let realSize = naturalSize.applying(transform)
                    loadedSize = CGSize(width: abs(realSize.width), height: abs(realSize.height))
                }
                
                // Wait with timeout to avoid indefinite blocking
                let waitResult = semaphore.wait(timeout: .now() + 5.0)
                if waitResult == .success {
                    size = loadedSize
                } else {
                    print("WARNING: Timeout loading video size for \(item.url.lastPathComponent)")
                }
            }
            
            DispatchQueue.main.async { [weak self] in
                self?.currentSize = size
            }
        }
    }
    
    func deleteCurrentItem() {
        guard currentIndex >= 0 && currentIndex < mediaItems.count else { return }
        
        // Capture values we need
        let itemToDelete = mediaItems[currentIndex]
        let indexToRemove = currentIndex
        
        // Perform deletion on background queue to avoid blocking UI
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            // CRITICAL: We MUST access the security scope of the specific file URL 
            // to move it to trash if it's outside our immediate sandbox or on an external drive.
            let didStartAccess = itemToDelete.url.startAccessingSecurityScopedResource()
            defer {
                if didStartAccess {
                    itemToDelete.url.stopAccessingSecurityScopedResource()
                }
            }
            
            let fileManager = FileManager.default
            
            do {
                // Move to Trash (macOS native way)
                // Note: We don't pre-check file existence to avoid TOCTOU race condition
                try fileManager.trashItem(at: itemToDelete.url, resultingItemURL: nil)
                
                // UI Update on main thread
                DispatchQueue.main.async { [weak self] in
                    self?.removeItemFromList(at: indexToRemove)
                }
                print("DELETED: \(itemToDelete.url.lastPathComponent)")
                
            } catch {
                // Handle the specific case where file doesn't exist
                let nsError = error as NSError
                if nsError.code == NSFileNoSuchFileError {
                    print("WARNING: File already deleted or moved: \(itemToDelete.url.lastPathComponent)")
                    // Still remove from list since file is gone
                    DispatchQueue.main.async { [weak self] in
                        self?.removeItemFromList(at: indexToRemove)
                    }
                } else {
                    print("ERROR: Could not move to trash: \(error.localizedDescription)")
                    DispatchQueue.main.async { [weak self] in
                        self?.lastError = .deleteFailed(error.localizedDescription)
                    }
                }
            }
        }
    }
    
    private func removeItemFromList(at index: Int) {
        // Ensure this runs on main thread since it modifies @Published properties
        DispatchQueue.main.async { [weak self] in
            guard let self = self else { return }
            guard index >= 0 && index < self.mediaItems.count else { return }
            
            self.mediaItems.remove(at: index)
            
            if self.mediaItems.isEmpty {
                self.currentIndex = -1
                self.currentSize = nil
            } else {
                // Keep index valid
                if self.currentIndex >= self.mediaItems.count {
                    self.currentIndex = self.mediaItems.count - 1
                }
                self.updateCurrentSize()
            }
            self.scanCount = self.mediaItems.count
        }
    }
}

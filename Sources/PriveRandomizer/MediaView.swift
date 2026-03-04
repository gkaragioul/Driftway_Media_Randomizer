import SwiftUI
import AVKit
import ImageIO

struct MediaView: View {
    let item: MediaItem
    @State private var currentTime: Double = 0
    @State private var duration: Double = 0
    @State private var isDragging: Bool = false
    @State private var sliderValue: Double = 0 // Separate state for slider to prevent feedback loop
    @State private var showVideoError: Bool = false
    
    var body: some View {
        ZStack {
            Color.black.edgesIgnoringSafeArea(.all)
            
            Group {
                if item.type == .image {
                    BetterImageView(url: item.url)
                } else if item.type == .video {
                    BetterVideoPlayerView(url: item.url, currentTime: $currentTime, duration: $duration, isDragging: isDragging, targetTime: $sliderValue, showError: $showVideoError)
                        .onChange(of: item.id) { _ in
                            // Reset video states when switching to a different item
                            currentTime = 0
                            duration = 0
                            sliderValue = 0
                            isDragging = false
                        }
                        .onChange(of: currentTime) { newTime in
                            if !isDragging {
                                sliderValue = newTime
                            }
                        }
                        .onChange(of: duration) { newDuration in
                            if newDuration > 0 && sliderValue > newDuration {
                                sliderValue = newDuration
                            }
                        }
                } else {
                    Text("Unsupported Media Type")
                        .foregroundColor(.white)
                }
            }
            .transition(.opacity)
            .id(item.id)
            
            // Video error overlay
            if item.type == .video && showVideoError {
                VStack {
                    Image(systemName: "exclamationmark.triangle")
                        .font(.system(size: 50))
                        .foregroundColor(.yellow)
                        .padding()
                    Text("Unable to play video")
                        .font(.headline)
                        .foregroundColor(.white)
                    Text(item.url.lastPathComponent)
                        .font(.caption)
                        .foregroundColor(.white.opacity(0.7))
                        .lineLimit(1)
                        .padding(.horizontal)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(Color.black.opacity(0.8))
            }
            
            // Custom Video Controls Overlay
            if item.type == .video && duration > 0.1 && !showVideoError { // Ensure duration is meaningful (>100ms)
                VStack {
                    Spacer()
                    HStack(spacing: 12) {
                        Text(formatTime(isDragging ? sliderValue : currentTime))
                            .font(.system(.caption, design: .monospaced))
                            .foregroundColor(.white)
                        
                        Slider(value: $sliderValue, in: 0...duration, onEditingChanged: { editing in
                            isDragging = editing
                            if !editing {
                                // When user releases, update the actual current time
                                currentTime = max(0, min(sliderValue, duration))
                            }
                        })
                        .accentColor(.blue)
                        
                        Text(formatTime(duration))
                            .font(.system(.caption, design: .monospaced))
                            .foregroundColor(.white)
                    }
                    .padding(.horizontal, 20)
                    .padding(.vertical, 10)
                    .background(
                        LinearGradient(gradient: Gradient(colors: [.clear, .black.opacity(0.6)]), startPoint: .top, endPoint: .bottom)
                    )
                }
            }
        }
    }
    
    private func formatTime(_ time: Double) -> String {
        guard time.isFinite && time >= 0 else { return "0:00" }
        
        // Handle edge case: very large durations (more than 24 hours)
        let totalSeconds = min(time, 86400) // Cap at 24 hours
        let hours = Int(totalSeconds) / 3600
        let minutes = (Int(totalSeconds) % 3600) / 60
        let seconds = Int(totalSeconds) % 60
        
        if hours > 0 {
            return String(format: "%d:%02d:%02d", hours, minutes, seconds)
        } else {
            return String(format: "%d:%02d", minutes, seconds)
        }
    }
}

// Using NSViewRepresentable for Images handles memory pressure and transitions more smoothly in AppKit
struct BetterImageView: NSViewRepresentable {
    let url: URL
    
    func makeNSView(context: Context) -> NSImageView {
        let imageView = NSImageView()
        // .scaleProportionallyUpOrDown is the standard for "Aspect Fit"
        imageView.imageScaling = .scaleProportionallyUpOrDown
        imageView.imageAlignment = .alignCenter
        imageView.imageFrameStyle = .none
        imageView.animates = true // Crucial for GIFs
        
        // Ensure the image view doesn't force a large size on its container
        imageView.setContentCompressionResistancePriority(.defaultLow, for: .horizontal)
        imageView.setContentCompressionResistancePriority(.defaultLow, for: .vertical)
        imageView.setContentHuggingPriority(.defaultLow, for: .horizontal)
        imageView.setContentHuggingPriority(.defaultLow, for: .vertical)
        
        return imageView
    }
    
    func updateNSView(_ nsView: NSImageView, context: Context) {
        // Only update if the URL has changed
        if context.coordinator.currentURL == url && nsView.image != nil {
            return
        }
        
        // Cancel any previous loading task
        context.coordinator.cancelLoading()
        context.coordinator.resetCancellation()
        
        nsView.image = nil
        context.coordinator.currentURL = url
        
        let currentURL = url // Capture URL for closure
        let isAnimatedImage = context.coordinator.isAnimatedImage(at: currentURL)
        
        // Create a loading task that can be cancelled
        let task = DispatchWorkItem { [weak coordinator = context.coordinator] in
            autoreleasepool {
                guard let coordinator = coordinator else { return }
                
                // Verify file still exists before attempting to load
                guard FileManager.default.fileExists(atPath: currentURL.path) else {
                    print("WARNING: Image file no longer exists: \(currentURL.lastPathComponent)")
                    return
                }
                
                // Thread-safe cancellation check
                guard !coordinator.checkCancelled() else { return }
                
                if isAnimatedImage {
                    // Animated formats (GIF/WebP/APNG/etc.) require full NSImage loading to preserve animation.
                    if let nsImage = NSImage(contentsOf: currentURL) {
                        DispatchQueue.main.async {
                            if coordinator.currentURL == currentURL && !coordinator.checkCancelled() {
                                nsView.image = nsImage
                            }
                        }
                    }
                } else {
                    // Optimized loading for static images
                    // kCGImageSourceCreateThumbnailWithTransform handles EXIF orientation (vertical/horizontal)
                    let options: [CFString: Any] = [
                        kCGImageSourceCreateThumbnailFromImageAlways: true,
                        kCGImageSourceShouldCacheImmediately: true,
                        kCGImageSourceCreateThumbnailWithTransform: true,
                        kCGImageSourceThumbnailMaxPixelSize: 4096 // Sufficient for 4K
                    ]
                    
                    guard let source = CGImageSourceCreateWithURL(currentURL as CFURL, nil),
                          let cgImage = CGImageSourceCreateThumbnailAtIndex(source, 0, options as CFDictionary) else {
                        
                        // Fallback to simpler loading if thumbnailing fails
                        // Check file exists again before fallback attempt
                        guard FileManager.default.fileExists(atPath: currentURL.path) else { return }
                        
                        guard !coordinator.checkCancelled() else { return }
                        
                        if let nsImage = NSImage(contentsOf: currentURL) {
                            DispatchQueue.main.async {
                                if coordinator.currentURL == currentURL && !coordinator.checkCancelled() {
                                    nsView.image = nsImage
                                }
                            }
                        }
                        return
                    }
                    
                    // CRITICAL FIX: Explicitly set the size to the pixel dimensions.
                    // If we use .zero, AppKit sometimes guesses based on screen scale, 
                    // which causes "zooming" or cropping if the logic doesn't match the pixels.
                    let pixelSize = CGSize(width: cgImage.width, height: cgImage.height)
                    let nsImage = NSImage(cgImage: cgImage, size: pixelSize)
                    
                    DispatchQueue.main.async {
                        // Final check to ensure we are still showing the right URL
                        if coordinator.currentURL == currentURL && !coordinator.checkCancelled() {
                            nsView.image = nsImage
                            // Force a redraw
                            nsView.needsDisplay = true
                        }
                    }
                }
            }
        }
        
        context.coordinator.loadingTask = task
        DispatchQueue.global(qos: .userInitiated).async(execute: task)
    }
    
    func makeCoordinator() -> Coordinator {
        Coordinator()
    }
    
    class Coordinator {
        var currentURL: URL?
        private(set) var isCancelled = false
        var loadingTask: DispatchWorkItem?
        let cancellationLock = NSLock()
        private var animationFrameCache: [URL: Bool] = [:]
        
        func cancelLoading() {
            cancellationLock.lock()
            isCancelled = true
            loadingTask?.cancel()
            loadingTask = nil
            cancellationLock.unlock()
        }
        
        func resetCancellation() {
            cancellationLock.lock()
            isCancelled = false
            cancellationLock.unlock()
        }
        
        func checkCancelled() -> Bool {
            cancellationLock.lock()
            let cancelled = isCancelled
            cancellationLock.unlock()
            return cancelled
        }
        
        func isAnimatedImage(at url: URL) -> Bool {
            if let cached = animationFrameCache[url] {
                return cached
            }
            
            guard let source = CGImageSourceCreateWithURL(url as CFURL, nil) else {
                animationFrameCache[url] = false
                return false
            }
            
            let frameCount = CGImageSourceGetCount(source)
            let isAnimated = frameCount > 1
            animationFrameCache[url] = isAnimated
            return isAnimated
        }
        
        deinit {
            cancelLoading()
        }
    }
}

struct BetterVideoPlayerView: NSViewRepresentable {
    let url: URL
    @Binding var currentTime: Double
    @Binding var duration: Double
    let isDragging: Bool
    @Binding var targetTime: Double // The time the user wants to seek to
    @Binding var showError: Bool // Whether to show error overlay
    
    func makeNSView(context: Context) -> AVPlayerView {
        let playerView = AVPlayerView()
        playerView.controlsStyle = .none // Cleaner look
        // Strict aspect ratio fitting (no cropping/zooming)
        playerView.videoGravity = .resizeAspect
        
        // Ensure it fits the container
        playerView.setContentCompressionResistancePriority(.defaultLow, for: .horizontal)
        playerView.setContentCompressionResistancePriority(.defaultLow, for: .vertical)
        
        return playerView
    }
    
    func updateNSView(_ nsView: AVPlayerView, context: Context) {
        if context.coordinator.currentURL != url {
            context.coordinator.cleanupPlayer()
            context.coordinator.currentURL = url
            context.coordinator.hasFailed = false // Reset error state
            
            let currentURL = url
            let coordinator = context.coordinator
            let parent = self
            
            // Reset error state when loading new video
            showError = false
            
            // Move file check and asset creation to background thread
            DispatchQueue.global(qos: .userInitiated).async {
                // Check if file exists before creating player
                guard FileManager.default.fileExists(atPath: currentURL.path) else {
                    print("ERROR: Video file does not exist: \(currentURL.lastPathComponent)")
                    DispatchQueue.main.async {
                        showError = true
                    }
                    return
                }
                
                let asset = AVAsset(url: currentURL)
                let playerItem = AVPlayerItem(asset: asset)
                let player = AVPlayer(playerItem: playerItem)
                
                DispatchQueue.main.async {
                    // Verify we still want to play this URL
                    guard coordinator.currentURL == currentURL else {
                        coordinator.cleanupPlayer()
                        return
                    }
                    
                    // Use weak reference in notification - will be removed in cleanupPlayer
                    NotificationCenter.default.addObserver(
                        coordinator,
                        selector: #selector(Coordinator.playerItemDidReachEnd),
                        name: .AVPlayerItemDidPlayToEndTime,
                        object: playerItem
                    )
                    
                    // Observe for playback errors
                    NotificationCenter.default.addObserver(
                        coordinator,
                        selector: #selector(Coordinator.playerItemFailedToPlayToEndTime),
                        name: .AVPlayerItemFailedToPlayToEndTime,
                        object: playerItem
                    )
                    
                    // Store reference to playerItem for cleanup
                    coordinator.currentPlayerItem = playerItem
                    
                    coordinator.setupPlayer(player, parent: parent)
                    nsView.player = player
                    player.play()
                }
            }
        }
        
        // Handle seeking when slider is dragged - only seek when not already seeking
        if isDragging && !context.coordinator.isSeeking {
            context.coordinator.seek(to: targetTime, in: nsView.player)
        }
    }
    
    static func dismantleNSView(_ nsView: AVPlayerView, coordinator: Coordinator) {
        coordinator.cleanupPlayer()
        nsView.player = nil
    }
    
    func makeCoordinator() -> Coordinator {
        Coordinator()
    }
    
    class Coordinator: NSObject {
        var currentURL: URL?
        private weak var player: AVPlayer?
        private var timeObserver: Any?
        private var seekWorkItem: DispatchWorkItem?
        private(set) var isSeeking: Bool = false
        var hasFailed: Bool = false
        private var parentView: BetterVideoPlayerView?
        fileprivate weak var currentPlayerItem: AVPlayerItem?
        
        func setupPlayer(_ newPlayer: AVPlayer, parent: BetterVideoPlayerView) {
            player = newPlayer
            parentView = parent
            addTimeObserver()
        }
        
        func cleanupPlayer() {
            seekWorkItem?.cancel()
            removeTimeObserver()
            parentView = nil
            
            // Remove notification observer using stored reference
            if let item = currentPlayerItem {
                NotificationCenter.default.removeObserver(self, name: .AVPlayerItemDidPlayToEndTime, object: item)
                NotificationCenter.default.removeObserver(self, name: .AVPlayerItemFailedToPlayToEndTime, object: item)
                currentPlayerItem = nil
            }
            
            if let player = player {
                player.pause()
                player.replaceCurrentItem(with: nil)
            }
            player = nil
            currentURL = nil
        }
        
        func seek(to time: Double, in player: AVPlayer?) {
            guard let player = player else { return }
            
            // Cancel any pending seek
            seekWorkItem?.cancel()
            
            // Debounce seeks to improve performance during slider drag
            let workItem = DispatchWorkItem { [weak self, weak player] in
                self?.isSeeking = true
                let targetTime = CMTime(seconds: time, preferredTimescale: 600)
                player?.seek(to: targetTime, toleranceBefore: .zero, toleranceAfter: .zero) { [weak self] _ in
                    self?.isSeeking = false
                }
            }
            
            seekWorkItem = workItem
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.05, execute: workItem)
        }
        
        @objc func playerItemDidReachEnd(notification: Notification) {
            player?.seek(to: .zero)
            player?.play()
        }
        
        @objc func playerItemFailedToPlayToEndTime(notification: Notification) {
            hasFailed = true
            if let error = notification.userInfo?[AVPlayerItemFailedToPlayToEndTimeErrorKey] as? Error {
                print("ERROR: Video playback failed: \(error.localizedDescription)")
            } else {
                print("ERROR: Video playback failed with unknown error")
            }
            // Update parent view's error state on main thread
            DispatchQueue.main.async { [weak self] in
                self?.parentView?.showError = true
            }
        }
        
        private func addTimeObserver() {
            let interval = CMTime(seconds: 0.1, preferredTimescale: CMTimeScale(NSEC_PER_SEC))
            timeObserver = player?.addPeriodicTimeObserver(forInterval: interval, queue: .main) { [weak self] time in
                guard let self = self, !self.isSeeking, let parent = self.parentView else { return }
                // Update the binding values with tolerance for floating point comparison
                let timeDiff = abs(time.seconds - parent.currentTime)
                if timeDiff > 0.05 { // 50ms tolerance
                    parent.currentTime = time.seconds
                }
                if let duration = self.player?.currentItem?.duration.seconds, duration.isFinite {
                    let durationDiff = abs(duration - parent.duration)
                    if durationDiff > 0.05 {
                        parent.duration = duration
                    }
                }
            }
        }
        
        private func removeTimeObserver() {
            if let observer = timeObserver {
                player?.removeTimeObserver(observer)
                timeObserver = nil
            }
        }
    }
}

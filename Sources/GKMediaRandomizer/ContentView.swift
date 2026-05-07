import SwiftUI
import AppKit
import UniformTypeIdentifiers

struct ContentView: View {
    @StateObject private var mediaManager = MediaManager()
    @State private var showFolderPicker = false
    @State private var showDeleteConfirmation = false
    @State private var itemToDelete: MediaItem?
    @State private var showErrorAlert = false
    
    var body: some View {
        ZStack {
            Color.black.edgesIgnoringSafeArea(.all)
            
            if mediaManager.isLoading {
                VStack {
                    ProgressView()
                    Text("Scanning folder...")
                        .foregroundColor(.white)
                        .padding()
                }
            } else if let currentItem = mediaManager.currentItem {
                MediaView(item: currentItem)
                    .transition(.opacity)
                    .id(currentItem.id)
            } else if mediaManager.mediaItems.isEmpty {
                VStack(spacing: 20) {
                    Image(systemName: "folder.badge.plus")
                        .font(.system(size: 50))
                        .foregroundColor(.blue)
                    
                    Text("Select a folder to start the random viewer")
                        .font(.headline)
                        .foregroundColor(.white)
                    
                    Button("Select Folder") {
                        selectFolder()
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.large)
                }
            }
            
            // Overlay controls
            VStack {
                HStack {
                    if !mediaManager.mediaItems.isEmpty {
                        VStack(alignment: .leading) {
                            Text(truncatedFileName(mediaManager.currentItem?.url.lastPathComponent ?? "", maxLength: 50))
                                .font(.caption)
                                .foregroundColor(.white.opacity(0.8))
                                .lineLimit(1)
                            Text("\(mediaManager.currentIndex + 1) / \(mediaManager.mediaItems.count)")
                                .font(.caption2)
                                .foregroundColor(.white.opacity(0.6))
                        }
                        .padding()
                        .background(Color.black.opacity(0.4))
                        .cornerRadius(8)
                        .padding()
                    }
                    Spacer()
                    
                    Button(action: selectFolder) {
                        Image(systemName: "folder")
                    }
                    .padding()
                    .background(Color.black.opacity(0.4))
                    .clipShape(Circle())
                    .padding()
                    
                    Button(action: {
                        mediaManager.toggleRandomizationMode()
                    }) {
                        Text(mediaManager.randomizationMode.rawValue)
                            .font(.caption2)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 6)
                    }
                    .background(Color.black.opacity(0.4))
                    .cornerRadius(8)
                    .padding(.trailing)
                }
                Spacer()
            }
        }
        .frame(minWidth: 800, minHeight: 600)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .onAppear {
            // Focus treatment or initial setup if needed
        }
        .onDrop(of: [.fileURL], isTargeted: nil) { providers in
            guard let provider = providers.first else { return false }
            
            provider.loadItem(forTypeIdentifier: UTType.fileURL.identifier, options: nil) { (urlData, error) in
                DispatchQueue.main.async { [weak mediaManager] in
                    if let error = error {
                        print("Drag and drop error: \(error)")
                        return
                    }
                    
                    guard let urlData = urlData as? Data,
                          let url = URL(dataRepresentation: urlData, relativeTo: nil) else {
                        print("Failed to parse dropped URL")
                        return
                    }
                    
                    var isDirectory: ObjCBool = false
                    if FileManager.default.fileExists(atPath: url.path, isDirectory: &isDirectory),
                       isDirectory.boolValue {
                        mediaManager?.startScanning(at: url)
                    } else {
                        print("Dropped item is not a directory: \(url.path)")
                    }
                }
            }
            return true
        }
        // Handle keyboard arrows and deletion
        .background(
            KeyEventHandlingView { key in
                switch key {
                case .rightArrow, .downArrow:
                    withAnimation {
                        mediaManager.next()
                    }
                case .leftArrow, .upArrow:
                    withAnimation {
                        mediaManager.previous()
                    }
                case .deleteItem:
                    if let currentItem = mediaManager.currentItem {
                        itemToDelete = currentItem
                        showDeleteConfirmation = true
                    }
                case .toggleFullscreen:
                    // Toggle fullscreen mode
                    if let window = NSApplication.shared.keyWindow {
                        window.toggleFullScreen(nil)
                    }
                case .exitFullscreen:
                    // Exit fullscreen if currently in fullscreen
                    if let window = NSApplication.shared.keyWindow, window.styleMask.contains(.fullScreen) {
                        window.toggleFullScreen(nil)
                    }
                case .playPause:
                    // Play/pause is handled by the video player internally
                    break
                default:
                    break
                }
            }
        )
        .alert("Move to Trash?", isPresented: $showDeleteConfirmation, presenting: itemToDelete) { item in
            Button("Cancel", role: .cancel) {}
            Button("Move to Trash", role: .destructive) {
                withAnimation {
                    mediaManager.deleteCurrentItem()
                }
            }
        } message: { item in
            Text("Are you sure you want to move '\(item.url.lastPathComponent)' to the Trash?")
        }
        .alert("Error", isPresented: $showErrorAlert) {
            Button("OK") {
                mediaManager.lastError = nil
            }
        } message: {
            Text(mediaManager.lastError?.localizedDescription ?? "An unknown error occurred")
        }
        .onChange(of: mediaManager.lastError) { error in
            showErrorAlert = error != nil
        }
    }
    
    private func truncatedFileName(_ name: String, maxLength: Int) -> String {
        // Use utf16 count for better compatibility with macOS file system
        let utf16Length = name.utf16.count
        guard utf16Length > maxLength else { return name }
        
        // Find the index that corresponds to maxLength-3 utf16 units
        var index = name.startIndex
        var count = 0
        let targetCount = maxLength - 3
        
        while index < name.endIndex && count < targetCount {
            let nextIndex = name.index(after: index)
            let utf16Count = name[index..<nextIndex].utf16.count
            if count + utf16Count > targetCount {
                break
            }
            count += utf16Count
            index = nextIndex
        }
        
        return String(name[name.startIndex..<index]) + "..."
    }
    
    private func selectFolder() {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = true
        panel.canChooseFiles = false
        
        if panel.runModal() == .OK {
            if let url = panel.url {
                mediaManager.startScanning(at: url)
            }
        }
    }
}

// Helper to handle keyboard events in SwiftUI
struct KeyEventHandlingView: NSViewRepresentable {
    enum Key {
        case leftArrow
        case rightArrow
        case upArrow
        case downArrow
        case deleteItem
        case toggleFullscreen
        case exitFullscreen
        case playPause
        case other
    }
    
    var onKey: (Key) -> Void
    
    func makeNSView(context: Context) -> NSView {
        let view = KeyView()
        view.onKey = onKey
        return view
    }
    
    func updateNSView(_ nsView: NSView, context: Context) {}
    
    static func dismantleNSView(_ nsView: NSView, coordinator: ()) {
        // Remove first responder status when view is dismantled
        nsView.window?.makeFirstResponder(nil)
    }
    
    class KeyView: NSView {
        var onKey: ((Key) -> Void)?
        private var hasBecomeFirstResponder = false
        
        deinit {
            // Clear the closure to break any retain cycles
            onKey = nil
        }
        
        override var acceptsFirstResponder: Bool { true }
        
        override func viewDidMoveToWindow() {
            // Only become first responder once to avoid stealing focus repeatedly
            if !hasBecomeFirstResponder, window != nil {
                hasBecomeFirstResponder = true
                window?.makeFirstResponder(self)
            }
        }
        
        override func viewWillMove(toWindow newWindow: NSWindow?) {
            super.viewWillMove(toWindow: newWindow)
            
            // If being removed from window, resign first responder
            if newWindow == nil, window != nil {
                window?.makeFirstResponder(nil)
            }
        }
        
        override func keyDown(with event: NSEvent) {
            let isCommandPressed = event.modifierFlags.contains(.command)
            
            switch event.keyCode {
            case 123: // Left arrow
                onKey?(.leftArrow)
            case 124: // Right arrow
                onKey?(.rightArrow)
            case 125: // Down arrow
                onKey?(.downArrow)
            case 126: // Up arrow
                onKey?(.upArrow)
            case 36: // Return/Enter
                onKey?(.toggleFullscreen)
            case 53: // Escape
                onKey?(.exitFullscreen)
            case 49: // Space
                onKey?(.playPause)
            case 51: // Backspace / Delete
                if isCommandPressed {
                    onKey?(.deleteItem)
                } else {
                    super.keyDown(with: event)
                }
            default:
                super.keyDown(with: event)
            }
        }
    }
}

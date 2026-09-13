package com.rsmaxwell.diaries.responder.utilities;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.attribute.BasicFileAttributes;
import java.text.Normalizer;
import java.util.ArrayList;
import java.util.Locale;

import com.rsmaxwell.diaries.responder.model.Image;

/** Portable user-path syntax and conservative, read-only resolution beneath a real Files root. */
public final class ImagePathPolicy {
    static final String STAGING = ".image-staging";
    private final Path root;

    public ImagePathPolicy(Path configuredRoot) throws IOException {
        root = configuredRoot.toRealPath();
        if (!Files.isDirectory(root)) throw new IOException("Files root is not a directory");
    }

    public Path root() { return root; }

    public String canonicalPath(String input) {
        String result = canonicalDirectory(input);
        Image.validateCanonicalRelativePath(result);
        return result;
    }

    /** Empty string denotes the root for directory guards; no URL decoding or traversal collapse. */
    public String canonicalDirectory(String input) {
        if (input == null) throw new IllegalArgumentException("Relative path is required");
        String portable = Normalizer.normalize(input.replace('\\', '/'), Normalizer.Form.NFC);
        if (portable.startsWith("/") || portable.contains(":"))
            throw new IllegalArgumentException("Absolute paths and URIs are forbidden");
        var segments = new ArrayList<String>();
        for (String part : portable.split("/", -1)) {
            if (part.equals("..")) throw new IllegalArgumentException("Path traversal is forbidden");
            if (part.isEmpty() || part.equals(".")) continue;
            validateSegment(part);
            if (part.equalsIgnoreCase(STAGING)) throw new IllegalArgumentException("Reserved upload directory");
            segments.add(part);
        }
        return String.join("/", segments);
    }

    public String uploadPath(String subdirectory, String filename) {
        if (filename == null || filename.isBlank() || filename.contains("/") || filename.contains("\\")
                || filename.equals(".") || filename.equals(".."))
            throw new IllegalArgumentException("Upload name must be a basename");
        String directory = canonicalDirectory(subdirectory);
        return canonicalPath((directory.isEmpty() ? "" : directory + "/") + filename);
    }

    private static void validateSegment(String value) {
        String stem = value.split("\\.", 2)[0].toUpperCase(Locale.ROOT);
        if (value.isBlank() || value.endsWith(".") || value.endsWith(" ")
                || value.codePoints().anyMatch(c -> Character.isISOControl(c) || "<>\"|?*".indexOf(c) >= 0)
                || stem.matches("CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³]"))
            throw new IllegalArgumentException("Non-portable path segment");
    }

    public Path resolve(String input) throws IOException {
        return resolveCanonical(canonicalPath(input));
    }

    public Path resolveDirectory(String input) throws IOException {
        return resolveCanonical(canonicalDirectory(input));
    }

    private Path resolveCanonical(String canonical) throws IOException {
        verifyRoot();
        Path current = root;
        if (canonical.isEmpty()) return current;
        for (String segment : canonical.split("/")) {
            if (Files.isDirectory(current, LinkOption.NOFOLLOW_LINKS)) {
                // Reject existing case/NFC aliases on either OS. Database folding remains authoritative.
                try (var children = Files.newDirectoryStream(current)) {
                    for (Path child : children) {
                        String actual = child.getFileName().toString();
                        if (Normalizer.normalize(actual, Normalizer.Form.NFC).equalsIgnoreCase(segment)
                                && !actual.equals(segment)) throw new IOException("Existing path has a case or Unicode alias");
                    }
                }
            }
            current = current.resolve(segment);
            if (Files.exists(current, LinkOption.NOFOLLOW_LINKS)) verifyEntry(current);
        }
        return current;
    }

    void verifyRoot() throws IOException {
        if (!root.toRealPath().equals(root) || !Files.isDirectory(root, LinkOption.NOFOLLOW_LINKS))
            throw new IOException("Files root identity changed");
    }

    static void verifyEntry(Path path) throws IOException {
        BasicFileAttributes attributes = Files.readAttributes(path, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        if (attributes.isSymbolicLink() || attributes.isOther() || !path.toRealPath().equals(path.toAbsolutePath().normalize()))
            throw new IOException("Symlinks and reparse-point aliases are forbidden beneath Files root");
    }

    /** Creates only validated parent directories, rechecking each component after creation. */
    public Path createParentDirectories(String canonical) throws IOException {
        Path target = resolve(canonical);
        Path current = root;
        for (Path segment : root.relativize(target.getParent())) {
            if (segment.toString().isEmpty()) continue;
            current = current.resolve(segment);
            if (!Files.exists(current, LinkOption.NOFOLLOW_LINKS)) {
                try { Files.createDirectory(current); }
                catch (java.nio.file.FileAlreadyExistsException concurrentCreation) { /* Validate below. */ }
            }
            verifyEntry(current);
            if (!Files.isDirectory(current, LinkOption.NOFOLLOW_LINKS)) throw new IOException("Parent is not a directory");
        }
        return resolve(canonical);
    }
}

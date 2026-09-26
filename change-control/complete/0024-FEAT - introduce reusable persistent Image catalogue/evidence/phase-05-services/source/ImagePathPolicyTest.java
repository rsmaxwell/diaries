package com.rsmaxwell.diaries.responder.utilities;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class ImagePathPolicyTest {
    @TempDir Path root;

    @Test void portableNormalizationPreservesLiteralCharactersAndCase() throws Exception {
        var policy = new ImagePathPolicy(root);
        assertEquals("Maps/Caf\u00e9 50%_1.png", policy.canonicalPath("Maps\\.\\Cafe\u0301 50%_1.png"));
        assertEquals("a/b/c.png", policy.canonicalPath("a//b/./c.png"));
        assertEquals("a/b", policy.canonicalDirectory("a\\b\\"));
        assertEquals("", policy.canonicalDirectory("./"));
        assertEquals("a..b.png", policy.uploadPath("", "a..b.png"));
        assertEquals("%2e%2e/file.png", policy.canonicalPath("%2e%2e/file.png"));
        assertEquals(root.toRealPath(), policy.resolveDirectory(""));
    }

    @Test void absoluteTraversalUriAndNonPortablePathsFailOnEveryOperatingSystem() throws Exception {
        var policy = new ImagePathPolicy(root);
        for (String invalid : List.of("/a", "\\a", "C:/a", "C:a", "\\\\server\\share\\a", "//server/share",
                "../a", "a/../b", "a\\..\\b", "https://host/a", "file:a", "a\u0000b", "a\nb",
                "CON.png", "x/NUL", "COM1.txt", "name.", "name ", "a*b", "a?b", "<a>", ".image-staging/x")) {
            assertThrows(IllegalArgumentException.class, () -> policy.resolve(invalid), invalid);
        }
        assertThrows(IllegalArgumentException.class, () -> policy.canonicalPath(""));
        for (String invalidName : List.of("", " ", ".", "..", "a/b", "a\\b"))
            assertThrows(IllegalArgumentException.class, () -> policy.uploadPath("folder", invalidName));
    }

    @Test void resolutionIsReadOnlyAndRejectsCaseAliases() throws Exception {
        var policy = new ImagePathPolicy(root);
        Path directory = Files.createDirectory(root.resolve("Maps"));
        Files.writeString(directory.resolve("Image.png"), "unchanged");
        assertThrows(IOException.class, () -> policy.resolve("maps/Image.png"));
        assertThrows(IOException.class, () -> policy.resolve("Maps/image.png"));
        assertEquals(directory.resolve("Image.png"), policy.resolve("Maps/Image.png"));
        assertEquals(root.resolve("missing/a.png"), policy.resolve("missing/a.png"));
        assertFalse(Files.exists(root.resolve("missing")));
        assertEquals("unchanged", Files.readString(directory.resolve("Image.png")));
    }

    @Test void symbolicLinksOrWindowsJunctionsCannotEscapeRoot() throws Exception {
        Path outside = Files.createTempDirectory(root.getParent(), "image-outside-");
        Path link = root.resolve("escape");
        try {
            Files.writeString(outside.resolve("sentinel.txt"), "unchanged");
            try { Files.createSymbolicLink(link, outside); }
            catch (IOException unavailable) {
                if (!System.getProperty("os.name").startsWith("Windows")) throw unavailable;
                Process junction = new ProcessBuilder("cmd.exe", "/c", "mklink", "/J", link.toString(), outside.toString())
                        .redirectErrorStream(true).start();
                String output = new String(junction.getInputStream().readAllBytes());
                assertEquals(0, junction.waitFor(), output);
            }
            var policy = new ImagePathPolicy(root);
            assertThrows(IOException.class, () -> policy.resolve("escape/sentinel.txt"));
            assertThrows(IOException.class, () -> policy.createParentDirectories("escape/new/file.png"));
            assertEquals("unchanged", Files.readString(outside.resolve("sentinel.txt")));
            assertFalse(Files.exists(outside.resolve("new")));
        } finally {
            Files.deleteIfExists(link);
            Files.deleteIfExists(outside.resolve("sentinel.txt"));
            Files.deleteIfExists(outside);
        }
    }
}

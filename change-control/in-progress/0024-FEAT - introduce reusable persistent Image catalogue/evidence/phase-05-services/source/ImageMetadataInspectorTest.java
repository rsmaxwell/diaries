package com.rsmaxwell.diaries.responder.utilities;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Stream;
import java.util.zip.CRC32;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.junit.jupiter.api.io.TempDir;

class ImageMetadataInspectorTest {
    @TempDir Path root;
    static byte[] fixture(String name) throws IOException {
        try (var in = ImageMetadataInspectorTest.class.getResourceAsStream("/image-inspection/" + name)) {
            assertNotNull(in, name);
            return in.readAllBytes();
        }
    }
    @TestFactory Stream<DynamicTest> supportedImagesAreDecodedRegardlessOfExtension() {
        return List.of("sample.jpg", "sample.png", "sample.gif", "sample.webp", "lossless.webp", "animated.gif", "animated.webp")
                .stream().map(name -> DynamicTest.dynamicTest(name, () -> {
                    byte[] bytes = fixture(name);
                    Path file = Files.write(root.resolve(name + ".txt"), bytes);
                    String mime = name.endsWith("jpg") ? "image/jpeg" : "image/" + name.substring(name.lastIndexOf('.') + 1);
                    var inspected = new ImageMetadataInspector().inspect(file, "application/octet-stream", null);
                    assertEquals(mime, inspected.image().orElseThrow().mimeType());
                    assertEquals(16, inspected.image().orElseThrow().width());
                    assertEquals(12, inspected.image().orElseThrow().height());
                    assertEquals(bytes.length, inspected.size());
                    assertEquals(ImageMetadataInspector.sha256(bytes), inspected.checksum());
                    assertEquals(inspected, new ImageMetadataInspector().inspect(file, mime.toUpperCase(), inspected.checksum().toUpperCase()));
                    String wrong = mime.equals("image/jpeg") ? "image/png" : "image/jpeg";
                    assertThrows(IOException.class, () -> new ImageMetadataInspector().inspect(file, wrong, null));
                }));
    }
    @TestFactory Stream<DynamicTest> truncatedSupportedContentIsRejectedEvenAsOctetStream() {
        return List.of("sample.jpg", "sample.png", "sample.gif", "sample.webp").stream().map(name ->
                DynamicTest.dynamicTest(name, () -> {
                    byte[] bytes = fixture(name);
                    Path file = Files.write(root.resolve(name), Arrays.copyOf(bytes, bytes.length - 5));
                    assertThrows(IOException.class, () -> new ImageMetadataInspector().inspect(file, "application/octet-stream", null));
                }));
    }
    @Test void genericBytesAndChecksumsHaveControlledOutcomes() throws Exception {
        Path file = Files.writeString(root.resolve("pretend.png"), "not an image");
        var inspector = new ImageMetadataInspector();
        assertTrue(inspector.inspect(file, "application/octet-stream", null).image().isEmpty());
        assertThrows(IOException.class, () -> inspector.inspect(file, "image/png", null));
        assertThrows(IOException.class, () -> inspector.inspect(file, "text/html", null));
        assertThrows(IOException.class, () -> inspector.inspect(file, null, "a".repeat(64)));
        assertThrows(IOException.class, () -> inspector.inspect(file, null, "not-a-hash"));
    }
    @Test void byteLimitIsInclusiveAndDecodeBudgetIsEnforcedBeforeAllocation() throws Exception {
        byte[] bytes = fixture("sample.png");
        Path file = Files.write(root.resolve("image.png"), bytes);
        assertTrue(new ImageMetadataInspector(bytes.length, 192).inspect(file, null, null).image().isPresent());
        assertThrows(IOException.class, () -> new ImageMetadataInspector(bytes.length - 1, 192).inspect(file, null, null));
        assertThrows(IOException.class, () -> new ImageMetadataInspector(bytes.length, 191).inspect(file, null, null));
    }
    @Test void crcCorruptionAndZeroDimensionsAreRejected() throws Exception {
        byte[] bytes = fixture("sample.png");
        bytes[29] ^= 1;
        Path file = Files.write(root.resolve("bad.png"), bytes);
        assertThrows(IOException.class, () -> new ImageMetadataInspector().inspect(file, null, null));
        bytes = fixture("sample.png");
        ByteBuffer.wrap(bytes, 16, 4).putInt(0);
        CRC32 crc = new CRC32(); crc.update(bytes, 12, 17);
        ByteBuffer.wrap(bytes, 29, 4).putInt((int) crc.getValue());
        Files.write(file, bytes);
        assertThrows(IOException.class, () -> new ImageMetadataInspector().inspect(file, null, null));
    }
}

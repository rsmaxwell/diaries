package com.rsmaxwell.diaries.responder.dto;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Consumer;

import org.eclipse.paho.mqttv5.client.IMqttToken;
import org.eclipse.paho.mqttv5.client.MqttAsyncClient;
import org.eclipse.paho.mqttv5.client.persist.MemoryPersistence;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;
import org.junit.jupiter.api.Test;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.rsmaxwell.diaries.responder.model.Base;
import com.rsmaxwell.diaries.responder.model.Image;

import jakarta.persistence.Column;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import jakarta.persistence.Table;

class ImageDtoTest {

	private static final ObjectMapper JSON = new ObjectMapper();

	private Image image() {
		return Image.builder().id(41L).version(3L).relativePath("Diary/Caf\u00e9 50%_1.png")
				.mimeType("image/png").originalFilename("Caf\u00e9 50%_1.png")
				.width(1200).height(800).checksum("a1".repeat(32))
				.caption("Harbour \u2014 1830").altText("A caf\u00e9 by the sea").build();
	}

	@Test
	void conversionsPreserveEveryValueIncludingIdentityAndVersion() throws Exception {
		Image source = image();
		ImageDBDTO db = new ImageDBDTO(source);
		ImagePublishDTO published = new ImagePublishDTO(db);
		assertEquals(source, new Image(db));
		assertEquals(source, new Image(published));
		assertEquals(db, new ImageDBDTO(published));
		assertEquals(published, new ImagePublishDTO(source));
		assertEquals(source, new Image(JSON.readValue(db.toJson(), ImageDBDTO.class)));
		assertEquals(source, new Image(JSON.readValue(published.toJson(), ImagePublishDTO.class)));
	}

	@Test
	void buildersAndNoArgConstructionDefaultCaptionsAndVersion() {
		assertEquals("", new Image().getCaption());
		assertEquals("", Image.builder().build().getAltText());
		assertEquals(0L, Image.builder().build().getVersion());
		assertEquals("", new ImageDBDTO().getCaption());
		assertEquals("", ImageDBDTO.builder().build().getAltText());
		assertEquals("", new ImagePublishDTO().getAltText());
		assertEquals("", ImagePublishDTO.builder().build().getCaption());
		assertThrows(NullPointerException.class, () -> new Image().setCaption(null));
		assertThrows(NullPointerException.class, () -> ImageDBDTO.builder().altText(null).build());
		assertThrows(NullPointerException.class, () -> new ImagePublishDTO().setAltText(null));
	}

	@Test
	void unsavedMetadataIsAllowedButCannotBePublishedWithoutIdentity() throws Exception {
		Image source = image();
		source.setId(null);
		assertDoesNotThrow(source::validate);
		assertTrue(JSON.readTree(new ImageDBDTO(source).toJson()).get("id").isNull());
		ImagePublishDTO dto = new ImagePublishDTO(source);
		assertThrows(IllegalArgumentException.class, dto::toJson);
		assertThrows(IllegalArgumentException.class, () -> dto.publish(new ConcurrentHashMap<>()));
		assertThrows(IllegalArgumentException.class, () -> dto.remove(new ConcurrentHashMap<>()));
	}

	@Test
	void metadataJsonHasExactlyTheTenContractFieldsAndUnicodeValues() throws Exception {
		ImagePublishDTO dto = new ImagePublishDTO(image());
		JsonNode node = JSON.readTree(dto.toJsonAsBytes());
		Set<String> names = new HashSet<>();
		node.fieldNames().forEachRemaining(names::add);
		assertEquals(Set.of("id", "version", "relativePath", "mimeType", "originalFilename",
				"width", "height", "checksum", "caption", "altText"), names);
		assertEquals(JSON.readTree(new ImageDBDTO(image()).toJson()), node);
		assertEquals("Diary/Caf\u00e9 50%_1.png", node.get("relativePath").textValue());
		assertEquals(1200, node.get("width").intValue());
		assertEquals(800, node.get("height").intValue());
		assertEquals(3, node.get("version").intValue());
		assertEquals("image/png", node.get("mimeType").textValue());
		assertEquals("a1".repeat(32), node.get("checksum").textValue());
		assertEquals("Harbour \u2014 1830", node.get("caption").textValue());
		assertEquals("A caf\u00e9 by the sea", node.get("altText").textValue());
		assertArrayEquals(dto.toJson().getBytes(StandardCharsets.UTF_8), dto.toJsonAsBytes());
	}

	@Test
	void mapPublicationAndIdentityOnlyTombstoneTouchOnlyCanonicalImageTopic() throws Exception {
		ConcurrentHashMap<String, String> map = new ConcurrentHashMap<>();
		map.put("diaries/fragments/41", "existing");
		ImagePublishDTO dto = new ImagePublishDTO(image());
		dto.publish(map);
		assertEquals(Set.of("diaries/images/41", "diaries/fragments/41"), map.keySet());
		assertEquals(dto.toJson(), map.get("diaries/images/41"));
		ImagePublishDTO.builder().id(41L).build().remove(map);
		assertEquals(Map.of("diaries/fragments/41", "existing"), map);
	}

	@Test
	void mqttMetadataAndTombstoneUsePublisherQosOneAndRetain() throws Exception {
		RecordingClient client = new RecordingClient();
		try {
			ImagePublishDTO dto = new ImagePublishDTO(image());
			dto.publish(client);
			assertEquals(1, client.calls);
			assertEquals("diaries/images/41", client.topic);
			assertArrayEquals(dto.toJsonAsBytes(), client.payload);
			assertEquals(1, client.qos);
			assertTrue(client.retained);
			ImagePublishDTO.builder().id(41L).build().remove(client);
			assertEquals(2, client.calls);
			assertEquals("diaries/images/41", client.topic);
			assertArrayEquals(new byte[0], client.payload);
			assertEquals(1, client.qos);
			assertTrue(client.retained);
		} finally { client.close(); }
	}

	@Test
	void nonCanonicalPathsAreRejectedWithoutNormalizationOrFilesystemAccess() {
		for (String path : List.of("", " ", "/absolute.png", "C:/image.png", "C:image.png",
				"\\\\server\\share\\image.png", "folder\\image.png", "../image.png", "a/../image.png",
				"a/./image.png", "a//image.png", "a/", "https://host/image.png", "a\nimage.png",
				"a\u0000image.png", "Cafe\u0301.png")) {
			Image source = image();
			source.setRelativePath(path);
			assertThrows(IllegalArgumentException.class, source::validate, path);
			assertThrows(IllegalArgumentException.class, () -> new ImageDBDTO(source), path);
		}
		Image source = image();
		source.setRelativePath(null);
		assertThrows(IllegalArgumentException.class, source::validate);
	}

	@Test
	void supportedMimesAndLiteralPercentUnderscorePathsRemainCasePreserving() {
		for (String mime : List.of("image/jpeg", "image/png", "image/gif", "image/webp")) {
			Image source = image();
			source.setMimeType(mime);
			assertDoesNotThrow(source::validate);
			assertEquals("Diary/Caf\u00e9 50%_1.png", source.getRelativePath());
		}
	}

	@Test
	void invalidMetadataCannotCrossConversionOrSerializationBoundaries() {
		List<Consumer<Image>> changes = List.of(i -> i.setWidth(0), i -> i.setHeight(-1),
				i -> i.setWidth(null), i -> i.setHeight(null), i -> i.setChecksum("A".repeat(64)),
				i -> i.setChecksum("g".repeat(64)), i -> i.setChecksum("a".repeat(63)),
				i -> i.setChecksum(null), i -> i.setMimeType("application/octet-stream"),
				i -> i.setMimeType("IMAGE/PNG"), i -> i.setMimeType(null),
				i -> i.setOriginalFilename(null), i -> i.setOriginalFilename("dir/image.png"),
				i -> i.setVersion(-1L), i -> i.setVersion(null), i -> i.setId(0L));
		for (Consumer<Image> change : changes) {
			Image source = image();
			change.accept(source);
			assertThrows(IllegalArgumentException.class, source::validate);
			assertThrows(IllegalArgumentException.class, () -> new ImagePublishDTO(source));
		}
		ImageDBDTO db = new ImageDBDTO(image());
		db.setHeight(0);
		assertThrows(IllegalArgumentException.class, () -> new Image(db));
		assertThrows(IllegalArgumentException.class, db::toJson);
		ImagePublishDTO published = new ImagePublishDTO(image());
		published.setRelativePath("/private/file.png");
		ConcurrentHashMap<String, String> map = new ConcurrentHashMap<>();
		assertThrows(IllegalArgumentException.class, () -> published.publish(map));
		assertTrue(map.isEmpty());
	}

	@Test
	void mappingMatchesPhaseTwoSqlAndValidationRunsBeforeJpaWrites() throws Exception {
		assertEquals(Base.class, Image.class.getSuperclass());
		assertEquals("image", Image.class.getAnnotation(Table.class).name());
		assertEquals("public", Image.class.getAnnotation(Table.class).schema());
		Map<String, String> columns = Map.of("relativePath", "relative_path", "mimeType", "mime_type",
				"originalFilename", "original_filename", "width", "width", "height", "height",
				"checksum", "checksum", "caption", "caption", "altText", "alt_text");
		for (var entry : columns.entrySet()) {
			Column column = Image.class.getDeclaredField(entry.getKey()).getAnnotation(Column.class);
			assertEquals(entry.getValue(), column.name());
			assertFalse(column.nullable());
		}
		assertEquals(String.class, Image.class.getDeclaredField("relativePath").getType());
		assertEquals("text", Image.class.getDeclaredField("relativePath").getAnnotation(Column.class).columnDefinition());
		assertEquals(127, Image.class.getDeclaredField("mimeType").getAnnotation(Column.class).length());
		assertEquals(64, Image.class.getDeclaredField("checksum").getAnnotation(Column.class).length());
		assertEquals(SqlTypes.CHAR, Image.class.getDeclaredField("checksum").getAnnotation(JdbcTypeCode.class).value());
		assertNotNull(Image.class.getMethod("validate").getAnnotation(PrePersist.class));
		assertNotNull(Image.class.getMethod("validate").getAnnotation(PreUpdate.class));
	}

	private static class RecordingClient extends MqttAsyncClient {
		String topic;
		byte[] payload;
		int qos;
		boolean retained;
		int calls;
		RecordingClient() throws Exception {
			super("tcp://localhost:1883", "image-dto-test", new MemoryPersistence());
		}
		@Override
		public IMqttToken publish(String topic, byte[] payload, int qos, boolean retained) {
			this.topic = topic;
			this.payload = payload;
			this.qos = qos;
			this.retained = retained;
			calls++;
			return null;
		}
	}
}

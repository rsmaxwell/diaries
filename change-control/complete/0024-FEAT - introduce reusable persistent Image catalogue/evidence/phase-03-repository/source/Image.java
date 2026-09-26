package com.rsmaxwell.diaries.responder.model;

import java.text.Normalizer;
import java.util.Set;

import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import com.rsmaxwell.diaries.responder.dto.ImageDBDTO;
import com.rsmaxwell.diaries.responder.dto.ImagePublishDTO;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;
import lombok.NonNull;
import lombok.ToString;
import lombok.experimental.SuperBuilder;

/** Metadata for one reusable file; independent of diary chronology. */
@Entity
@Table(name = "image", schema = "public")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
public class Image extends Base {

	private static final Set<String> SUPPORTED_MIME_TYPES =
			Set.of("image/jpeg", "image/png", "image/gif", "image/webp");

	@Column(name = "relative_path", nullable = false, columnDefinition = "text")
	private String relativePath;

	@Column(name = "mime_type", nullable = false, length = 127)
	private String mimeType;

	@Column(name = "original_filename", nullable = false, columnDefinition = "text")
	private String originalFilename;

	@Column(name = "width", nullable = false)
	private Integer width;

	@Column(name = "height", nullable = false)
	private Integer height;

	@JdbcTypeCode(SqlTypes.CHAR)
	@Column(name = "checksum", nullable = false, length = 64)
	private String checksum;

	@Builder.Default
	@NonNull
	@Column(name = "caption", nullable = false, columnDefinition = "text DEFAULT ''")
	private String caption = "";

	@Builder.Default
	@NonNull
	@Column(name = "alt_text", nullable = false, columnDefinition = "text DEFAULT ''")
	private String altText = "";

	public Image(ImageDBDTO dto) {
		this.id = dto.getId();
		this.version = dto.getVersion();
		this.relativePath = dto.getRelativePath();
		this.mimeType = dto.getMimeType();
		this.originalFilename = dto.getOriginalFilename();
		this.width = dto.getWidth();
		this.height = dto.getHeight();
		this.checksum = dto.getChecksum();
		this.caption = dto.getCaption();
		this.altText = dto.getAltText();
		validate();
	}

	public Image(ImagePublishDTO dto) {
		this.id = dto.getId();
		this.version = dto.getVersion();
		this.relativePath = dto.getRelativePath();
		this.mimeType = dto.getMimeType();
		this.originalFilename = dto.getOriginalFilename();
		this.width = dto.getWidth();
		this.height = dto.getHeight();
		this.checksum = dto.getChecksum();
		this.caption = dto.getCaption();
		this.altText = dto.getAltText();
		validate();
	}

	/**
	 * Service-boundary validation, also enforced before JPA writes.
	 * This checks already-canonical metadata; it does not resolve files, decode
	 * images or implement database case folding. Those belong to the services.
	 */
	@PrePersist
	@PreUpdate
	public void validate() {
		if (id != null && id <= 0) {
			throw new IllegalArgumentException("Image id must be positive when present");
		}
		if (version == null || version < 0) {
			throw new IllegalArgumentException("Image version must be non-negative");
		}
		validateCanonicalRelativePath(relativePath);
		if (mimeType == null || !SUPPORTED_MIME_TYPES.contains(mimeType)) {
			throw new IllegalArgumentException("Image MIME type is unsupported");
		}
		if (width == null || height == null || width <= 0 || height <= 0) {
			throw new IllegalArgumentException("Image dimensions must be positive");
		}
		if (checksum == null || !checksum.matches("[0-9a-f]{64}")) {
			throw new IllegalArgumentException("Image checksum must contain 64 lowercase hexadecimal characters");
		}
		if (originalFilename == null || originalFilename.isBlank()
				|| originalFilename.indexOf('/') >= 0 || originalFilename.indexOf('\\') >= 0
				|| originalFilename.indexOf(':') >= 0
				|| originalFilename.codePoints().anyMatch(Character::isISOControl)) {
			throw new IllegalArgumentException("Image originalFilename must be a filename without a directory");
		}
		if (caption == null || altText == null) {
			throw new IllegalArgumentException("Image caption and altText must not be null");
		}
	}

	/** Shared syntax check for persisted metadata and repository lookup arguments. */
	public static void validateCanonicalRelativePath(String relativePath) {
		if (relativePath == null || relativePath.isBlank()
				|| relativePath.indexOf('\\') >= 0 || relativePath.indexOf(':') >= 0
				|| relativePath.codePoints().anyMatch(Character::isISOControl)
				|| !Normalizer.isNormalized(relativePath, Normalizer.Form.NFC)) {
			throw new IllegalArgumentException("Image relativePath must be a canonical NFC relative path");
		}
		for (String segment : relativePath.split("/", -1)) {
			if (segment.isEmpty() || segment.equals(".") || segment.equals("..")) {
				throw new IllegalArgumentException("Image relativePath contains an invalid path segment");
			}
		}
	}
}

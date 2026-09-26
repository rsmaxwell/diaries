package com.rsmaxwell.diaries.responder.dto;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.rsmaxwell.diaries.responder.model.Base;
import com.rsmaxwell.diaries.responder.model.Image;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;
import lombok.NonNull;
import lombok.ToString;
import lombok.experimental.SuperBuilder;

/** Persistence metadata; relativePath remains a portable String. */
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
public class ImageDBDTO extends Base implements Jsonable {

	private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

	private String relativePath;

	private String mimeType;

	private String originalFilename;

	private Integer width;

	private Integer height;

	private String checksum;

	@Builder.Default
	@NonNull
	private String caption = "";

	@Builder.Default
	@NonNull
	private String altText = "";

	public ImageDBDTO(Image image) {
		image.validate();
		this.id = image.getId();
		this.version = image.getVersion();
		this.relativePath = image.getRelativePath();
		this.mimeType = image.getMimeType();
		this.originalFilename = image.getOriginalFilename();
		this.width = image.getWidth();
		this.height = image.getHeight();
		this.checksum = image.getChecksum();
		this.caption = image.getCaption();
		this.altText = image.getAltText();
	}

	public ImageDBDTO(ImagePublishDTO dto) {
		this(new Image(dto));
	}

	/** Validates mutable/builder/deserialized DTOs before crossing a boundary. */
	public void validate() {
		new Image(this);
	}

	@Override
	public String toJson() throws JsonProcessingException {
		validate();
		return OBJECT_MAPPER.writeValueAsString(this);
	}

	@Override
	public byte[] toJsonAsBytes() throws JsonProcessingException {
		validate();
		return OBJECT_MAPPER.writeValueAsBytes(this);
	}

}

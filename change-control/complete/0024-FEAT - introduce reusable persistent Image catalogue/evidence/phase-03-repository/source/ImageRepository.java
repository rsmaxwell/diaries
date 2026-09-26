package com.rsmaxwell.diaries.responder.repository;

import java.util.Optional;

import com.rsmaxwell.diaries.responder.dto.ImageDBDTO;
import com.rsmaxwell.diaries.responder.model.Image;

public interface ImageRepository extends CrudRepository<Image, ImageDBDTO, Long> {

	Optional<ImageDBDTO> findByRelativePath(String canonicalPath);

	Iterable<ImageDBDTO> findAllOrderedByRelativePath();

	/** Exact path or slash-delimited descendants; empty String represents Files root. */
	boolean existsAtOrBelow(String canonicalPath);

	/** Raw SQL predicates are not supported; use the bound lookup methods. */
	@Override
	Iterable<ImageDBDTO> find(String where);
}

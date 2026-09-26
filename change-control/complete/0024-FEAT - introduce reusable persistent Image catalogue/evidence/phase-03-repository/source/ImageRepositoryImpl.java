package com.rsmaxwell.diaries.responder.repositoryImpl;

import java.util.List;
import java.util.Objects;
import java.util.Optional;

import org.hibernate.Session;
import org.hibernate.query.CommonQueryContract;
import org.hibernate.query.NativeQuery;

import com.rsmaxwell.diaries.responder.dto.ImageDBDTO;
import com.rsmaxwell.diaries.responder.model.Image;
import com.rsmaxwell.diaries.responder.repository.ImageRepository;

import jakarta.persistence.EntityManager;
import jakarta.persistence.TransactionRequiredException;

/** Bound PostgreSQL queries. Transactions and retained publication belong to callers. */
public class ImageRepositoryImpl implements ImageRepository {

	private static final String SELECT = "SELECT id, version, relative_path, mime_type, original_filename, "
			+ "width, height, checksum, caption, alt_text FROM public.image";
	private static final String FOLDED_PATH = "lower(relative_path COLLATE pg_catalog.pg_unicode_fast)";
	private static final String PATH_PARAMETER = "lower(cast(:path AS text) COLLATE pg_catalog.pg_unicode_fast)";
	private static final String ORDER = " ORDER BY " + FOLDED_PATH + ", relative_path COLLATE \"C\", id";
	private final EntityManager entityManager;

	public ImageRepositoryImpl(EntityManager entityManager) {
		this.entityManager = Objects.requireNonNull(entityManager, "entityManager");
	}

	private Session session() {
		return entityManager.unwrap(Session.class);
	}

	private void requireTransaction() {
		if (!entityManager.getTransaction().isActive()) {
			throw new TransactionRequiredException("Image writes require a caller-owned transaction");
		}
	}

	private static void requireId(Long id) {
		if (id == null || id <= 0) {
			throw new IllegalArgumentException("Image id must be positive");
		}
	}

	@Override
	public Long getId(Object value) {
		if (!(value instanceof Long id)) {
			throw new IllegalArgumentException("Expected a PostgreSQL bigint Image id");
		}
		requireId(id);
		return id;
	}

	@Override
	public long count() {
		return session().createNativeQuery("SELECT count(*) FROM public.image", Long.class).getSingleResult();
	}

	@Override
	public boolean existsById(Long id) {
		requireId(id);
		return session().createNativeQuery("SELECT EXISTS(SELECT 1 FROM public.image WHERE id=:id)", Boolean.class)
				.setParameter("id", id).getSingleResult();
	}

	@Override
	public Optional<ImageDBDTO> findById(Long id) {
		requireId(id);
		return single(session().createNativeQuery(SELECT + " WHERE id=:id", Object[].class).setParameter("id", id));
	}

	@Override
	public Optional<ImageDBDTO> findByRelativePath(String canonicalPath) {
		Image.validateCanonicalRelativePath(canonicalPath);
		return single(session().createNativeQuery(SELECT + " WHERE " + FOLDED_PATH + "=" + PATH_PARAMETER, Object[].class)
				.setParameter("path", canonicalPath));
	}

	@Override
	public Iterable<ImageDBDTO> findAll() {
		return findAllOrderedByRelativePath();
	}

	@Override
	public List<ImageDBDTO> findAllOrderedByRelativePath() {
		return session().createNativeQuery(SELECT + ORDER, Object[].class).getResultList().stream().map(this::newDTO).toList();
	}

	@Override
	public Iterable<ImageDBDTO> find(String where) {
		throw new UnsupportedOperationException("Raw SQL predicates are not supported for Images; use bound lookup methods");
	}

	@Override
	public boolean existsAtOrBelow(String canonicalPath) {
		if ("".equals(canonicalPath)) {
			return session().createNativeQuery("SELECT EXISTS(SELECT 1 FROM public.image)", Boolean.class).getSingleResult();
		}
		Image.validateCanonicalRelativePath(canonicalPath);
		String pattern = canonicalPath.replace("!", "!!").replace("%", "!%").replace("_", "!_") + "/%";
		String sql = "SELECT EXISTS(SELECT 1 FROM public.image WHERE " + FOLDED_PATH + "=" + PATH_PARAMETER
				+ " OR " + FOLDED_PATH + " LIKE lower(cast(:pattern AS text) COLLATE pg_catalog.pg_unicode_fast) ESCAPE '!')";
		return session().createNativeQuery(sql, Boolean.class).setParameter("path", canonicalPath)
				.setParameter("pattern", pattern).getSingleResult();
	}

	@Override
	public <S extends Image> Long save(S entity) {
		entity.validate();
		if (entity.getId() != null) {
			throw new IllegalArgumentException("Save requires a new Image without an id; use update for existing Images");
		}
		requireTransaction();
		var query = session().createNativeQuery("""
				INSERT INTO public.image(version,relative_path,mime_type,original_filename,width,height,checksum,caption,alt_text)
				VALUES (:version,:path,:mime,:filename,:width,:height,:checksum,:caption,:altText) RETURNING id
				""", Long.class);
		bindMetadata(query, entity);
		Long id = getId(query.getSingleResult());
		entity.setId(id);
		return id;
	}

	/** Matches existing CRUD semantics: persists the version supplied by the caller. */
	@Override
	public <S extends Image> int update(S entity) {
		entity.validate();
		requireId(entity.getId());
		requireTransaction();
		var query = session().createNativeMutationQuery("""
				UPDATE public.image SET version=:version, relative_path=:path, mime_type=:mime,
				original_filename=:filename, width=:width, height=:height, checksum=:checksum,
				caption=:caption, alt_text=:altText WHERE id=:id
				""");
		bindMetadata(query, entity);
		query.setParameter("id", entity.getId());
		return query.executeUpdate();
	}

	private static void bindMetadata(CommonQueryContract query, Image entity) {
		query.setParameter("version", entity.getVersion());
		query.setParameter("path", entity.getRelativePath());
		query.setParameter("mime", entity.getMimeType());
		query.setParameter("filename", entity.getOriginalFilename());
		query.setParameter("width", entity.getWidth());
		query.setParameter("height", entity.getHeight());
		query.setParameter("checksum", entity.getChecksum());
		query.setParameter("caption", entity.getCaption());
		query.setParameter("altText", entity.getAltText());
	}

	@Override
	public int delete(Image entity) {
		return deleteById(entity.getId());
	}

	@Override
	public int deleteById(Long id) {
		requireId(id);
		requireTransaction();
		return session().createNativeMutationQuery("DELETE FROM public.image WHERE id=:id").setParameter("id", id).executeUpdate();
	}

	@Override
	public int deleteAll() {
		requireTransaction();
		return session().createNativeMutationQuery("DELETE FROM public.image").executeUpdate();
	}

	private Optional<ImageDBDTO> single(NativeQuery<Object[]> query) {
		List<Object[]> rows = query.getResultList();
		if (rows.size() > 1) {
			throw new IllegalStateException("Image lookup is ambiguous; verify the catalogue unique index");
		}
		return rows.isEmpty() ? Optional.empty() : Optional.of(newDTO(rows.get(0)));
	}

	public ImageDBDTO newDTO(Object[] row) {
		if (row.length != 10) {
			throw new IllegalArgumentException("Expected the ten-column Image projection");
		}
		ImageDBDTO dto = ImageDBDTO.builder().id(((Number) row[0]).longValue()).version(((Number) row[1]).longValue())
				.relativePath((String) row[2]).mimeType((String) row[3]).originalFilename((String) row[4])
				.width(((Number) row[5]).intValue()).height(((Number) row[6]).intValue())
				.checksum((String) row[7]).caption((String) row[8]).altText((String) row[9]).build();
		dto.validate();
		return dto;
	}
}

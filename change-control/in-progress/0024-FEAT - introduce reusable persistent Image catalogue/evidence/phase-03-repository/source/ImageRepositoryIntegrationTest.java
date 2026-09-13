package com.rsmaxwell.diaries.responder.repositoryImpl;

import static org.junit.jupiter.api.Assertions.*;

import java.util.List;

import org.hibernate.SessionFactory;
import org.hibernate.cfg.Configuration;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;

import com.rsmaxwell.diaries.responder.dto.ImageDBDTO;
import com.rsmaxwell.diaries.responder.model.Image;

import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceException;
import jakarta.persistence.TransactionRequiredException;

/** Opt-in against the isolated PostgreSQL 18 fixture; never uses application config. */
@EnabledIfEnvironmentVariable(named = "DIARIES_IMAGE_REPOSITORY_TEST_URL", matches = ".+")
class ImageRepositoryIntegrationTest {

	private static SessionFactory factory;
	private EntityManager em;
	private ImageRepositoryImpl repository;

	@BeforeAll
	static void connect() {
		String url = System.getenv("DIARIES_IMAGE_REPOSITORY_TEST_URL");
		assertTrue(url.matches("jdbc:postgresql://127\\.0\\.0\\.1:[0-9]+/image_repository_test"),
				"Only the isolated loopback image_repository_test database is accepted");
		factory = new Configuration().addAnnotatedClass(Image.class)
				.setProperty("hibernate.connection.url", url)
				.setProperty("hibernate.connection.username", "diaries")
				.setProperty("hibernate.connection.password", "")
				.setProperty("hibernate.hbm2ddl.auto", "validate")
				.setProperty("hibernate.show_sql", "false")
				.buildSessionFactory();
	}

	@BeforeEach
	void begin() {
		em = factory.createEntityManager();
		repository = new ImageRepositoryImpl(em);
		em.getTransaction().begin();
		assertEquals(0, repository.count(), "Fixture must be empty; each test rolls back");
	}

	@AfterEach
	void rollback() {
		if (em != null) {
			if (em.getTransaction().isActive()) { em.getTransaction().rollback(); }
			em.close();
		}
	}

	@AfterAll
	static void close() {
		if (factory != null) { factory.close(); }
	}

	private Image image(String path) {
		return Image.builder().relativePath(path).mimeType("image/png")
				.originalFilename(path.substring(path.lastIndexOf('/') + 1)).width(30).height(20)
				.checksum("a".repeat(64)).caption("O'Brien's caf\u00e9").altText("A \u00a3 sign").build();
	}

	@Test
	void saveFindUpdateDeleteRoundTripsEveryColumnAndMatchesJpaMapping() {
		Image image = image("Diary/First.PNG");
		Long id = repository.save(image);
		assertEquals(id, image.getId());
		assertTrue(id > 0);
		assertTrue(repository.existsById(id));
		assertEquals(image, new Image(repository.findById(id).orElseThrow()));
		assertEquals(image, em.find(Image.class, id));
		em.clear();
		image.setVersion(1L);
		image.setRelativePath("Other/Renamed.png");
		image.setMimeType("image/webp");
		image.setOriginalFilename("original.webp");
		image.setWidth(91);
		image.setHeight(83);
		image.setChecksum("b".repeat(64));
		image.setCaption("new 'caption'");
		image.setAltText("");
		assertEquals(1, repository.update(image));
		assertEquals(image, new Image(repository.findById(id).orElseThrow()));
		assertTrue(repository.findByRelativePath("Diary/First.PNG").isEmpty());
		assertEquals(1, repository.delete(image));
		assertEquals(0, repository.deleteById(id));
		assertFalse(repository.existsById(id));
		assertTrue(repository.findById(id).isEmpty());
		assertEquals(0, repository.update(image));
	}

	@Test
	void caseAliasesUseTheSameUnicodeExpressionAsTheUniqueIndex() {
		Image saved = image("Folder/CAF\u00c9.PNG");
		repository.save(saved);
		assertEquals(saved.getId(), repository.findByRelativePath("folder/caf\u00e9.png").orElseThrow().getId());
		assertTrue(repository.existsAtOrBelow("FOLDER"));
		assertTrue(repository.existsAtOrBelow("folder/caf\u00e9.png"));
		assertThrows(PersistenceException.class, () -> repository.save(image("folder/caf\u00e9.png")));
	}

	@Test
	void subtreeMatchingHonoursSegmentBoundaries() {
		repository.save(image("album/nested/photo.png"));
		assertTrue(repository.existsAtOrBelow("album"));
		assertTrue(repository.existsAtOrBelow("ALBUM/nested"));
		assertFalse(repository.existsAtOrBelow("al"));
		assertFalse(repository.existsAtOrBelow("albums"));
		assertFalse(repository.existsAtOrBelow("album/nest"));
		assertFalse(repository.existsAtOrBelow("album/nested/photo.png/child"));
		assertTrue(repository.findByRelativePath("album").isEmpty());
	}

	@Test
	void percentUnderscoreAndEscapeMarkerAreLiteralInSubtreeLookups() {
		repository.save(image("wildX/sub/photo.png"));
		assertFalse(repository.existsAtOrBelow("wild%"));
		assertFalse(repository.existsAtOrBelow("wild_"));
		repository.save(image("wild%_/sub/photo.png"));
		assertTrue(repository.existsAtOrBelow("wild%_"));
		repository.save(image("wow!_/sub/photo.png"));
		assertTrue(repository.existsAtOrBelow("wow!_"));
		assertFalse(repository.existsAtOrBelow("wow!%"));
	}

	@Test
	void quotesAndSqlLookingTextStayBoundData() {
		String path = "O'Brien/quote' OR '1'='1.png";
		Image saved = image(path);
		repository.save(saved);
		assertEquals(saved, new Image(repository.findByRelativePath(path).orElseThrow()));
		assertTrue(repository.existsAtOrBelow("O'Brien"));
		assertFalse(repository.existsAtOrBelow("' OR '1'='1"));
		assertTrue(repository.findByRelativePath("' OR '1'='1").isEmpty());
		assertEquals(1, repository.count());
		assertThrows(UnsupportedOperationException.class, () -> repository.find("1=1; DELETE FROM image"));
	}

	@Test
	void orderedListingAndDuplicateChecksumsAreDeterministic() {
		repository.save(image("Zulu.png"));
		repository.save(image("beta.png"));
		repository.save(image("Alpha.png"));
		assertEquals(List.of("Alpha.png", "beta.png", "Zulu.png"), repository.findAllOrderedByRelativePath()
				.stream().map(ImageDBDTO::getRelativePath).toList());
		assertEquals(repository.findAllOrderedByRelativePath(), repository.findAll());
		assertEquals(3, repository.count());
		assertEquals(3, repository.deleteAll());
		assertEquals(0, repository.count());
		assertFalse(repository.existsAtOrBelow(""));
	}

	@Test
	void emptyRootAndMissingPathsHaveExplicitBehaviour() {
		assertFalse(repository.existsAtOrBelow(""));
		assertTrue(repository.findByRelativePath("missing.png").isEmpty());
		assertTrue(repository.findAllOrderedByRelativePath().isEmpty());
		repository.save(image("root.png"));
		assertTrue(repository.existsAtOrBelow(""));
		assertThrows(IllegalArgumentException.class, () -> repository.findByRelativePath(""));
	}

	@Test
	void invalidPathsAndMetadataAreRejectedBeforeQueries() {
		for (String path : List.of("/absolute", "C:/absolute", "../outside", "a/../b", "a//b", "a/", "a\\b", "Cafe\u0301.png")) {
			assertThrows(IllegalArgumentException.class, () -> repository.findByRelativePath(path));
			assertThrows(IllegalArgumentException.class, () -> repository.existsAtOrBelow(path));
		}
		assertThrows(IllegalArgumentException.class, () -> repository.existsAtOrBelow(null));
		assertThrows(IllegalArgumentException.class, () -> repository.findById(0L));
		Image invalid = image("bad.png");
		invalid.setChecksum("' OR 1=1 --");
		assertThrows(IllegalArgumentException.class, () -> repository.save(invalid));
		assertEquals(0, repository.count());
	}

	@Test
	void callerRollbackRemovesSavedRowsAndWritesRequireATransaction() {
		Image saved = image("rollback.png");
		repository.save(saved);
		assertEquals(1, repository.count());
		em.getTransaction().rollback();
		assertEquals(0, repository.count());
		assertThrows(TransactionRequiredException.class, () -> repository.save(image("outside.png")));
		assertThrows(TransactionRequiredException.class, () -> repository.update(saved));
		assertThrows(TransactionRequiredException.class, () -> repository.deleteById(saved.getId()));
		assertThrows(TransactionRequiredException.class, repository::deleteAll);
	}

	@Test
	void updateCannotCreateACaseAliasOfAnotherImage() {
		Image first = image("first.png");
		Image second = image("second.png");
		repository.save(first);
		repository.save(second);
		assertThrows(IllegalArgumentException.class, () -> repository.save(first));
		second.setRelativePath("FIRST.PNG");
		assertThrows(PersistenceException.class, () -> repository.update(second));
	}
}

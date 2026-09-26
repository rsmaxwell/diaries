package com.rsmaxwell.diaries.responder;

import static org.junit.jupiter.api.Assertions.*;

import java.net.URI;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;

import com.rsmaxwell.diaries.responder.config.Config;
import com.rsmaxwell.diaries.responder.config.DbConfig;
import com.rsmaxwell.diaries.responder.config.Jdbc;
import com.rsmaxwell.diaries.responder.config.User;
import com.rsmaxwell.diaries.responder.model.Image;
import com.rsmaxwell.diaries.responder.repositoryImpl.ImageRepositoryImpl;
import com.rsmaxwell.diaries.responder.utilities.DiaryContext;
import com.rsmaxwell.diaries.responder.utilities.GetEntityManager;

import jakarta.persistence.EntityManager;
import jakarta.persistence.EntityManagerFactory;
import jakarta.persistence.PersistenceException;

/** Uses the production factory and startup wiring with a dedicated restored database. */
@EnabledIfEnvironmentVariable(named = "DIARIES_IMAGE_WIRING_TEST_URL", matches = ".+")
class ImageWiringIntegrationTest {

	private static EntityManagerFactory factory;
	private static Config config;
	private static List<?> chronologyBefore;
	private EntityManager em;
	private DiaryContext context;

	@BeforeAll
	static void start() {
		String url = System.getenv("DIARIES_IMAGE_WIRING_TEST_URL");
		assertTrue(url.matches("jdbc:postgresql://127\\.0\\.0\\.1:[0-9]+/image_wiring_test"));
		URI uri = URI.create(url.substring(5));
		Jdbc jdbc = new Jdbc();
		jdbc.setDbms("postgresql");
		jdbc.setDriver("org.postgresql.Driver");
		User user = new User();
		user.setUsername("diaries");
		user.setPassword("");
		DbConfig db = new DbConfig();
		db.setJdbc(jdbc);
		db.setHost(uri.getHost());
		db.setPort(uri.getPort());
		db.setDatabase("image_wiring_test");
		db.setAdmin(user);
		db.setUsers(List.of(user));
		db.setAdditionalConnectionProperties(Map.of("hibernate.hbm2ddl.auto", "validate"));
		config = new Config();
		config.setDb(db);
		config.setRefreshPeriod("10s");
		config.setRefreshExpiration("60s");
		factory = GetEntityManager.adminFactory(db);
		chronologyBefore = chronology();
	}

	@BeforeEach
	void wire() throws Exception {
		em = factory.createEntityManager();
		context = Responder.createContext(config, factory, em);
		assertEquals(0, context.getImageRepository().count());
	}

	@AfterEach
	void cleanup() {
		if (em != null) {
			if (em.getTransaction().isActive()) { em.getTransaction().rollback(); }
			// Only this new fixture's Image rows: helper tests intentionally commit.
			em.getTransaction().begin();
			context.getImageRepository().deleteAll();
			em.getTransaction().commit();
			em.close();
		}
	}

	@AfterAll
	static void stop() {
		if (factory != null) {
			try { assertEquals(chronologyBefore, chronology()); }
			finally { factory.close(); }
		}
	}

	private static List<?> chronology() {
		try (EntityManager reader = factory.createEntityManager()) {
			return reader.createNativeQuery("""
					SELECT md5(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]')) FROM public.diary t
					UNION ALL SELECT md5(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]')) FROM public.page t
					UNION ALL SELECT md5(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]')) FROM public.fragment t
					UNION ALL SELECT md5(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]')) FROM public.marquee t
					""", String.class).getResultList();
		}
	}

	private Image candidate(String path) {
		return Image.builder().relativePath(path).mimeType("image/png").originalFilename("image.png")
				.width(5).height(6).checksum("a".repeat(64)).build();
	}

	@Test
	void actualFactoryAndResponderWiringRegisterAndExposeImage() {
		assertEquals(1, factory.getMetamodel().getEntities().stream().filter(e -> e.getJavaType() == Image.class).count());
		assertInstanceOf(ImageRepositoryImpl.class, context.getImageRepository());
		assertSame(factory, context.getEntityManagerFactory());
		assertSame(em, context.getEntityManager());
		assertNotNull(context.getDiaryRepository());
		assertNotNull(context.getPageRepository());
		assertNotNull(context.getPersonRepository());
		assertNotNull(context.getFragmentRepository());
		assertNotNull(context.getMarqueeRepository());
		assertEquals(10, context.getRefreshPeriod());
		assertEquals(60, context.getRefreshExpiration());
	}

	@Test
	void saveAndUpdateCommitBeforeReturningAndInflateIndependently() throws Exception {
		Image source = candidate("wiring/image.png");
		Image saved = context.saveImage(source);
		assertNull(source.getId());
		assertFalse(em.getTransaction().isActive());
		try (EntityManager reader = factory.createEntityManager()) {
			assertEquals(saved, reader.find(Image.class, saved.getId()));
		}
		saved.setCaption("Updated");
		saved.setVersion(1L);
		assertEquals(1, context.updateImage(saved));
		assertEquals(saved, context.inflateImage(saved.getId()));
		assertThrows(Exception.class, () -> context.inflateImage(Long.MAX_VALUE));
	}

	@Test
	void uniqueConflictRollsBackAndContextRemainsUsable() throws Exception {
		Image first = context.saveImage(candidate("wiring/image.png"));
		Image duplicate = candidate("WIRING/IMAGE.PNG");
		assertThrows(PersistenceException.class, () -> context.saveImage(duplicate));
		assertNull(duplicate.getId());
		assertFalse(em.getTransaction().isActive());
		assertEquals(1, context.getImageRepository().count());
		assertEquals(first, context.inflateImage(first.getId()));
		assertNotNull(context.saveImage(candidate("other.png")).getId());
	}

	@Test
	void activeTransactionRemainsOwnedByCaller() {
		em.getTransaction().begin();
		assertThrows(IllegalStateException.class, () -> context.saveImage(candidate("nested.png")));
		assertTrue(em.getTransaction().isActive());
		assertEquals(0, context.getImageRepository().count());
	}

	@Test
	void imageWritesDoNotAlterExistingRetainedReplayInPhaseThree() throws Exception {
		Map<String, String> before = context.loadFromDatabase();
		context.saveImage(candidate("unreferenced.png"));
		assertEquals(before, context.loadFromDatabase());
		assertTrue(before.keySet().stream().noneMatch(t -> t.startsWith("diaries/images/")));
	}
}

package com.rsmaxwell.diaries.responder.utilities;

import static org.junit.jupiter.api.Assertions.*;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Proxy;
import java.util.Optional;

import org.junit.jupiter.api.Test;

import com.rsmaxwell.diaries.responder.dto.ImageDBDTO;
import com.rsmaxwell.diaries.responder.model.Image;
import com.rsmaxwell.diaries.responder.repository.ImageRepository;

import jakarta.persistence.EntityManager;
import jakarta.persistence.EntityTransaction;

class DiaryContextImageTest {

	private Image candidate() {
		return Image.builder().relativePath("diary/image.png").originalFilename("image.png")
				.mimeType("image/png").width(4).height(5).checksum("a".repeat(64)).build();
	}

	@Test
	void inflationIsIndependentOfChronologyAndReportsMissingImage() throws Exception {
		DiaryContext context = new DiaryContext();
		Image saved = candidate();
		saved.setId(51L);
		ImageDBDTO dto = new ImageDBDTO(saved);
		context.setImageRepository(proxy(ImageRepository.class, (p, m, a) -> Optional.of(dto)));
		assertEquals(saved, context.inflateImage(51L));
		assertEquals(saved, context.inflateImage(dto));
		context.setImageRepository(proxy(ImageRepository.class, (p, m, a) -> Optional.empty()));
		assertEquals("Image not found: id: 99", assertThrows(Exception.class, () -> context.inflateImage(99L)).getMessage());
	}

	@Test
	void saveReturnsCopyOnlyAfterCommitAndLeavesCallerUntouched() throws Exception {
		Fixture fixture = new Fixture();
		Image source = candidate();
		Image result = fixture.context.saveImage(source);
		assertEquals(51L, result.getId());
		assertNull(source.getId());
		assertNotSame(source, result);
		assertEquals(1, fixture.begins);
		assertEquals(1, fixture.commits);
		assertEquals(0, fixture.rollbacks);
		assertFalse(fixture.active);
	}

	@Test
	void updatePreservesProvidedVersionAndReturnsAffectedCount() throws Exception {
		Fixture fixture = new Fixture();
		Image source = candidate();
		source.setId(51L);
		source.setVersion(8L);
		assertEquals(1, fixture.context.updateImage(source));
		assertEquals(8L, fixture.written.getVersion());
		assertNotSame(source, fixture.written);
		assertEquals(8L, source.getVersion());
		assertEquals(1, fixture.commits);
	}

	@Test
	void repositoryFailureRollsBackWithoutAssigningCallerIdentity() {
		Fixture fixture = new Fixture();
		fixture.operationFailure = new Exception("insert failed after identity assignment");
		Image source = candidate();
		assertSame(fixture.operationFailure, assertThrows(Exception.class, () -> fixture.context.saveImage(source)));
		assertNull(source.getId());
		assertEquals(1, fixture.rollbacks);
		assertEquals(0, fixture.commits);
		assertFalse(fixture.active);
	}

	@Test
	void commitFailureCannotReturnSuccessAndPreservesRollbackFailure() {
		Fixture fixture = new Fixture();
		fixture.commitFailure = new IllegalStateException("commit failed");
		fixture.rollbackFailure = new IllegalStateException("rollback failed");
		Image source = candidate();
		Throwable failure = assertThrows(IllegalStateException.class, () -> fixture.context.saveImage(source));
		assertSame(fixture.commitFailure, failure);
		assertArrayEquals(new Throwable[] { fixture.rollbackFailure }, failure.getSuppressed());
		assertNull(source.getId());
		assertEquals(1, fixture.rollbacks);
	}

	@Test
	void activeCallerTransactionIsNeitherCommittedNorRolledBack() {
		Fixture fixture = new Fixture();
		fixture.active = true;
		assertThrows(IllegalStateException.class, () -> fixture.context.saveImage(candidate()));
		assertEquals(0, fixture.begins);
		assertEquals(0, fixture.commits);
		assertEquals(0, fixture.rollbacks);
		assertNull(fixture.written);
		assertTrue(fixture.active);
	}

	@Test
	void failedBeginDoesNotAttemptRollback() {
		Fixture fixture = new Fixture();
		fixture.beginFailure = new IllegalStateException("begin failed");
		assertSame(fixture.beginFailure, assertThrows(IllegalStateException.class, () -> fixture.context.saveImage(candidate())));
		assertEquals(0, fixture.rollbacks);
		assertNull(fixture.written);
	}

	@Test
	void invalidMetadataNeverStartsATransaction() {
		Fixture fixture = new Fixture();
		Image source = candidate();
		source.setWidth(0);
		assertThrows(IllegalArgumentException.class, () -> fixture.context.saveImage(source));
		assertEquals(0, fixture.begins);
	}

	private static class Fixture {
		final DiaryContext context = new DiaryContext();
		boolean active;
		int begins, commits, rollbacks;
		Image written;
		Exception operationFailure;
		RuntimeException beginFailure, commitFailure, rollbackFailure;
		Fixture() {
			EntityTransaction tx = proxy(EntityTransaction.class, (p, m, a) -> {
				switch (m.getName()) {
				case "isActive": return active;
				case "begin": begins++; if (beginFailure != null) { throw beginFailure; } active = true; return null;
				case "commit": commits++; if (commitFailure != null) { throw commitFailure; } active = false; return null;
				case "rollback": rollbacks++; if (rollbackFailure != null) { throw rollbackFailure; } active = false; return null;
				default: throw new UnsupportedOperationException(m.getName());
				}
			});
			context.setEntityManager(proxy(EntityManager.class, (p, m, a) -> {
				if (m.getName().equals("getTransaction")) { return tx; }
				throw new UnsupportedOperationException(m.getName());
			}));
			context.setImageRepository(proxy(ImageRepository.class, (p, m, a) -> {
				assertTrue(active);
				written = (Image) a[0];
				if (m.getName().equals("save")) { written.setId(51L); }
				if (operationFailure != null) { throw operationFailure; }
				if (m.getName().equals("save")) { return 51L; }
				if (m.getName().equals("update")) { return 1; }
				throw new UnsupportedOperationException(m.getName());
			}));
		}
	}

	@SuppressWarnings("unchecked")
	private static <T> T proxy(Class<T> type, InvocationHandler handler) {
		return (T) Proxy.newProxyInstance(type.getClassLoader(), new Class<?>[] { type }, handler);
	}
}

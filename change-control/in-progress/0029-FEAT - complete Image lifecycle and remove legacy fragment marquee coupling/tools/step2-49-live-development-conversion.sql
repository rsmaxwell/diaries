-- 0029-FEAT approved 49-source development-only conversion.
-- For fixed target diaries-development-db ONLY, with IDE responder stopped,
-- verified backup and explicit operator approval. Never use against production.
-- SQL statements are identical to the successfully tested isolated rehearsal.
\set ON_ERROR_STOP on
BEGIN;
SET LOCAL lock_timeout = '10s';
SET LOCAL statement_timeout = '120s';
CREATE TEMP TABLE reviewed_0029 (
  source_id bigint PRIMARY KEY, destination_page_id bigint NOT NULL,
  image_id bigint NOT NULL, diary_id bigint NOT NULL,
  html_md5 text NOT NULL, image_checksum text NOT NULL, caption text NOT NULL,
  disposition text NOT NULL, year integer NOT NULL, month integer NOT NULL,
  day integer NOT NULL, seq numeric NOT NULL
) ON COMMIT DROP;
INSERT INTO reviewed_0029 VALUES
(84,692,3,1,'f8d05c41bd2932cf757a1bb0093dc887','71263a0b4b8ed3bac18dd650d841c165a58f23d11717f7399b1139811b7b10fc','Whitley Park','EXISTING_LINK_VERIFY',1828,3,20,1.0),
(96,693,4,1,'ea6f050e163a6db36ed7cc5347dec453','59ae61501c15ff90c7dcdca936f69e21df79b9e10eb69e6cd292b18ab73b45e3','Commercial Hotel','SINGLE_CANDIDATE_REVIEW',1828,3,31,1.0),
(114,694,5,1,'3ddd09f1c264a9366089588daf36427c','f7b2daf4007a56e8aa119b293234c6ee9c0234d2d1c29e5af2119c692e599363','Broomville House','PAGE_FILENAME_STRONG_CANDIDATE',1828,4,17,1.0),
(115,694,6,1,'f98158f989daba1cb776b176cb525e9b','4acf577d243ce05a2c08d2488259a31c0eeb0acc66aec77617d26f04d202c2ad','Clogrennane House','PAGE_FILENAME_STRONG_CANDIDATE',1828,4,17,2.0),
(116,694,7,1,'e46c98d54390d4ec24bca25d8106bc0f','36ae5f4a7754a442dd7337ed43b5dfd36840da2f144fb4d468611103f9cc5e3c','Map of Carlow','PAGE_FILENAME_STRONG_CANDIDATE',1828,4,17,3.0),
(117,694,8,1,'b05424f59bddc780bbb2fb37e107aa29','5bf81f82865c6700942dea91c9117865cdf49273ea0d3c30f455709cae2c222c','Map of Dublin','PAGE_FILENAME_STRONG_CANDIDATE',1828,4,17,4.0),
(118,694,9,1,'727d8becc9373c36715dd8464b52673d','ad972fda62fde0f7c29684f1608ad99b538d018101b8bf5efb9ea5d7579a7da4','Map of journey from Tynemouth to Carlow','PAGE_FILENAME_STRONG_CANDIDATE',1828,4,17,5.0),
(226,704,10,1,'28325f1c9f3b3d9b92080a1f7c1accc5','e2b8a8cf5df7f5681acc55f043713d50a25eb080c0da4c57107603a8109c316a','The Black Middens','SINGLE_CANDIDATE_REVIEW',1828,8,1,1.0),
(233,704,11,1,'41ba63db77b05540e834dab028e049a4','0ec31e8bfe5f8366f3580a8e08d9eb37bdd09f52d076936b559dd0028f76c56a','The first voyage of ''Hope''','SINGLE_CANDIDATE_REVIEW',1828,8,7,1.0),
(257,707,12,1,'d9a9c9f95ff7ce6b5e2285052bdacd3c','d9239e70d7f84c9e98caf73660abec0960e47bbd9039e88199955db2fc98346b','Appuldurcombe House','SINGLE_CANDIDATE_REVIEW',1828,8,30,1.0),
(258,707,13,1,'2bb1cba383394729b662dbdb26387d5f','594de2ed7619fe911e142b0d528269689a279d5dae5413ff2f9487ac1bb5ddc9','Isle of Wight','SINGLE_CANDIDATE_REVIEW',1828,8,30,2.0),
(259,707,15,1,'4396e3e1881de6c049438ae165019be5','c678e0bd6c488e3eec86d669f5066bedfc2e1671b3a172931f14568e852c00d1','Navarino House','SINGLE_CANDIDATE_REVIEW',1828,8,30,3.0),
(260,707,14,1,'d40c9272230d848419d23ee842983519','3d3b0c79daa11713ad6b6003c56f18672e9d29cf1ce75fafe2ca7a59ead9564e','Map showing Navarino House','SINGLE_CANDIDATE_REVIEW',1828,8,30,4.0),
(310,712,16,1,'3b7c62f453ad74786d045b6012b72dca','ba21a37708dcaeddad11e2d8f5b555da92681afaecce1d08a9dcd90c8df12000','Map Alnwick and Tyneside','SINGLE_CANDIDATE_REVIEW',1828,10,17,1.0),
(544,737,72,1,'80755dfe6cf5255afd012ae7693d55bd','20aa37569ac2b4f962ed3e74b3e51b17f01b931ae516bcb7f10816f7e56b4d01','Baltic map','SINGLE_CANDIDATE_REVIEW',1829,6,5,1.0),
(545,737,73,1,'e4a8368faf47b38504e16273d25b1c06','b729a3bab407829192cada11efaa037014fa93825689717a254e625efd01581b','Copenhagen large map','SINGLE_CANDIDATE_REVIEW',1829,6,5,2.0),
(546,737,74,1,'071fd7b214d8cec96ee165909ffb076c','42ef8db9a0e6a84fbb727805aa7e179c5e7a8aa89228c23d4e9358ff9d237249','Copenhagen map','SINGLE_CANDIDATE_REVIEW',1829,6,5,3.0),
(547,737,75,1,'2eb57110a8a44ff1e570aa5993da1c93','a75e829a447b054b108bc47dd46fcd380f8aa4ab07e6342e8de15df1dacfe075','Copenhagen east','SINGLE_CANDIDATE_REVIEW',1829,6,5,4.0),
(565,743,75,1,'60dd00cd201403be413c7c5ca99a5af7','a75e829a447b054b108bc47dd46fcd380f8aa4ab07e6342e8de15df1dacfe075','Voyage east from Copenhagen','PAGE_FILENAME_STRONG_CANDIDATE',1829,6,20,5.0),
(575,744,76,1,'2635c5dc4b42d9c498312de982523afd','cd0a4a5b1d066ff8ea0fdaa959cde758f8476c037844982a61c246b6d0fdb0d3','Voyage for Copenhagen to St Petersburg','PAGE_FILENAME_STRONG_CANDIDATE',1829,6,26,1.0),
(578,745,17,1,'af2a695910b0775cc923b084083c4f0e','13b3ced34b2c6d80e84cffb07b0f2c8bc53977852163aa01220c004df7192051','Kopu Lighthouse','SINGLE_CANDIDATE_REVIEW',1829,6,27,1.0),
(593,752,22,1,'4a7929f8c404eec8b3716a35aeee0ebc','3ef33432b43bd47c882c838a71409d4ae82d275c0ae2f06177a594b4a6957c4e','Peter and Paul Cathedral, St Petersburg','SINGLE_CANDIDATE_REVIEW',1829,7,7,1.0),
(594,752,78,1,'03bbca67b111933f2110ed8f6e67b200','ddabf0f09024690f6b0a434e2bdf7437ca055ace8928e199ac7ce6c0ca3d7945','St Petersburg map','SINGLE_CANDIDATE_REVIEW',1829,7,7,2.0),
(595,752,77,1,'8f2110e78df34b9c18c4b6a23910374c','25a4eaed075620efed1f33d7c7fffbccbce92a06c17def03f0ebd8df33c13e45','Large St Petersburg map','SINGLE_CANDIDATE_REVIEW',1829,7,7,3.0),
(596,752,19,1,'7a6fa2dd237dbde874b93e85a8f73f2f','c3abd851e52f272f7981a94f7a6256c352cf4aa7530676e1d811e1782d5b19c2','Room Plan','SINGLE_CANDIDATE_REVIEW',1829,7,7,4.0),
(598,752,18,1,'7c955bc3b85b2ae089cde13cba43c7db','9cbe68505a023ad9db4898914c5bf763cce4fb33b6689364586350d58d6411e0','Hermitage','PAGE_FILENAME_STRONG_CANDIDATE',1829,7,8,1.0),
(599,752,21,1,'45e33a46485c68ef735f288d0c885974','3f5d54daa8129b47f6f9e1c99ec74cc3997bdb439f30cae80e5e50fccec0cc08','Hermitage','PAGE_FILENAME_STRONG_CANDIDATE',1829,7,8,2.0),
(600,752,20,1,'ed7083ac2c5c914873da61511f6db37b','ed3d8e5b54a5db4fc7ac5ed35e6d0371ca878842d495e6aa6793ac9985f9969a','Hermitage from the front','PAGE_FILENAME_STRONG_CANDIDATE',1829,7,8,3.0),
(606,755,25,1,'a397ecaa55a1c637b58d2575033d6f0c','2097979bd1ca47370a55c0f6053167a96f541a5c04adfe4ff52dc564ccc97d5a','St Isaac church','SINGLE_CANDIDATE_REVIEW',1829,7,11,1.0),
(611,756,24,1,'cf8abe0cdbe80d440d44e738c0e81a69','ced43ee148a94330eab04fdfda53bffc434d034416eb9250acfc659b47049294','main entrance to Alexander Nevsky Lavra monastery','SEQUENCE_CONTEXT_PROVISIONAL',1829,7,14,1.0),
(612,756,23,1,'90b849836f2a5d4fea2a56de499c83c2','d8113b8c819fabfcc9bd6cf1bfceafff41df606ef8425032ef4fe6b6e359bd7e','interior of the Alexander Nevsky Lavra monastery','SEQUENCE_CONTEXT_PROVISIONAL',1829,7,14,2.0),
(613,756,26,1,'86d9b6a5aaef160774d62cbd52b27fc3','31de4c6b22cf16b5f59cbeb61ae1ba1c7d37794c65e2e171ea27fce88f6504b7','monastery at Alexander Nevsky Lavra','SEQUENCE_CONTEXT_PROVISIONAL',1829,7,14,3.0),
(632,761,27,1,'d27f0163e1e312602334f17fe273223b','05983c068288df798767a4d2e9e6382c050a9e82fddcd638d93aaafb8c729661','Commodore Trunnion and Jack Hatchway','SINGLE_CANDIDATE_REVIEW',1829,7,29,1.0),
(633,761,28,1,'273e4ed022332cc73b441bb23adb7194','7cdc755fcfcdcacbe2d4bbe143bdaa5bf9cb7c0cc000a9473ec13f06849c96eb','Peregrine Pickle 1st edition','SINGLE_CANDIDATE_REVIEW',1829,7,29,2.0),
(679,772,80,1,'9e52191dab8c47463c9c0ad9fead32c7','7f9c48beec78daa43c189ccc4b91c18568521ef77c87acde12086dc547951354','Map of London','SINGLE_CANDIDATE_REVIEW',1829,9,5,1.0),
(680,772,2,1,'4f57177686fa57ba9f28e775b2a73ec9','64f403ad983210663aaab2d46c4b642a445bca568b9341b33926543e33327ed8','Bugsby''s Hole','SINGLE_CANDIDATE_REVIEW',1829,9,5,2.0),
(683,772,30,1,'c51ffd7538bf0479e84e0303cc948167','a715322c3905830da061b3d3ed1ad2c77957c695914991b9fc6818da01562c0d','The Cock, Fleet Street, London','SINGLE_CANDIDATE_REVIEW',1829,9,7,1.0),
(684,772,29,1,'a2a4e87871e62d4311770d196e21cd2e','5601e921f5dc947b6777a57229362409711683995bf15105aa7e7e79bf7ffaf7','The White Horse, Fetter Lane, London','SINGLE_CANDIDATE_REVIEW',1829,9,7,2.0),
(720,778,81,1,'de8ad1a0a52b3d4d0df1f8235b6847a2','176b69a1e56dd694db6bc94bc499cf541dc22500084566834a175ea2c21fbd1b','Burnhopeside Hall','SINGLE_CANDIDATE_REVIEW',1829,10,10,1.0),
(722,778,31,1,'c8e6f71ce6d4ea21df6d5846ee2f12fa','a35cc6244aa64a5a0635b8168e92a952a57d4ccb9d017272c28281e3fabe4217','Lanchester Church','SINGLE_CANDIDATE_REVIEW',1829,10,11,1.0),
(725,779,32,1,'917bfa886745f1df2ffacfb1b826cc16','317fee10813e9d10f4f9c25ad3a3fa0b10c82fc84707d5895425140874da5218','The Kings Head Lanchester','SINGLE_CANDIDATE_REVIEW',1829,10,13,1.0),
(739,780,1,1,'eebd6739c89e3be4b137aed5e0d00f37','7306fd420df902de56be5b61ff448219d2b286ac1ef3abb4cabdbf74aa82d9bb','Lucia Elizabeth Vestris','SINGLE_CANDIDATE_REVIEW',1829,10,26,1.0),
(809,788,35,1,'ca739a596b216f6fe10330ce97b16e70','095e7d4f6c19a7ccdcbc7cc5daae84a14964d245ae2d759598a19cd2722bb73e','The Tynemouth Lodge Hotel','SINGLE_CANDIDATE_REVIEW',1830,1,3,1.0),
(980,827,40,2,'5888c130ea685d3048484ef2fef92529','2b78908744912b54b3798456f186b1645d4b7b2e3c07d022986f590675540249','','SINGLE_CANDIDATE_REVIEW',1830,6,23,1.0),
(1029,840,41,2,'0e5f53a64d233460e4fc50602f54f890','7a59e2e49e5b14fae0e31064e79653222a5a602b8191949232a9fd3d939c9f4d','','SINGLE_CANDIDATE_REVIEW',1830,8,10,1.0),
(1030,840,42,2,'9b04e5daa05b9ef2dc21a48c29ea1aef','025b0a15b81b5ce5199a5f8a520cab7a1a16fd50fa7f7f559f2581e89eb8301e','','SINGLE_CANDIDATE_REVIEW',1830,8,10,2.0),
(1043,843,43,2,'0e98b62639be8f354dc176f8d4b7f6b0','99d82348670d4ced7d21c53a15df2b467566c5a44e52ba87b49318c31ee377e1','Archangel','SINGLE_CANDIDATE_REVIEW',1830,8,22,1.0),
(1182,874,46,3,'82c4b6f92454c4dd50fa7e1ce3a81963','4a0ebe6350670d3af3dc2eead956ce9f4e3a04f45b7da1b29ebf492fb2292637','Doodle on blotting paper','SINGLE_CANDIDATE_REVIEW',1831,1,5,1.0),
(1933,1066,71,5,'2c2116cee854b9d1507763aaf3ef23ef','a16d0efc9d4ca32b5abbe141a3db0ff772e67477327a13ea0ea670e326f445c5','Burnhopeside Hall','SINGLE_CANDIDATE_REVIEW',1834,1,7,1.0);
DO $gate$
DECLARE bad bigint;
BEGIN
 IF (SELECT count(*) FROM reviewed_0029)<>49
    OR (SELECT count(*) FROM reviewed_0029 WHERE disposition='EXISTING_LINK_VERIFY')<>1
 THEN RAISE EXCEPTION '0029 manifest cardinality/disposition mismatch'; END IF;
 SELECT count(*) INTO bad FROM reviewed_0029 m
 LEFT JOIN fragment f ON f.id=m.source_id
 LEFT JOIN image i ON i.id=m.image_id
 LEFT JOIN page p ON p.id=m.destination_page_id
 WHERE f.id IS NULL OR f.page_id IS NOT NULL OR f.type IS NOT NULL
 OR md5(f.text)<>m.html_md5
 OR f.year<>m.year OR f.month<>m.month OR f.day<>m.day OR f.sequence<>m.seq
 OR i.id IS NULL OR i.checksum<>m.image_checksum
 OR p.id IS NULL OR p.diary_id<>m.diary_id;
 IF bad<>0 THEN RAISE EXCEPTION '0029 migration precheck failed: % mismatches',bad; END IF;
 IF NOT EXISTS (SELECT 1 FROM fragment WHERE id=2338 AND page_id=692
     AND type='IMAGE' AND image_id=3 AND year=1828 AND month=3 AND day=20)
 THEN RAISE EXCEPTION '0029 Whitley Park existing IMAGE link drift'; END IF;
 IF EXISTS (SELECT 1 FROM reviewed_0029 m JOIN fragment f
   ON f.page_id=m.destination_page_id AND f.year=m.year AND f.month=m.month
   AND f.day=m.day AND f.image_id=m.image_id AND f.type='IMAGE'
   WHERE m.source_id<>84)
 THEN RAISE EXCEPTION '0029 pre-existing IMAGE conversion collision'; END IF;
END $gate$;
-- Preserve complete original source rows in the development database audit archive.
CREATE TABLE public.migration0029_legacy_image_archive AS
 SELECT f.* FROM fragment f JOIN reviewed_0029 m ON m.source_id=f.id;
ALTER TABLE public.migration0029_legacy_image_archive
 ADD PRIMARY KEY (id);
-- This authorised development conversion retains complete original HTML and metadata
-- in the audit archive, with source-to-destination receipts for review.
CREATE TABLE public.migration0029_rehearsal_receipt AS
 SELECT m.*, transaction_timestamp() AS rehearsed_at FROM reviewed_0029 m;
ALTER TABLE public.migration0029_rehearsal_receipt
 ADD PRIMARY KEY (source_id);
-- Existing Whitley Park IMAGE fragment 2338 remains authoritative.
-- Remove ONLY its redundant legacy HTML source after archive and guards.
DELETE FROM fragment WHERE id=84;
-- Convert remaining 48 source rows in place (preserving identity/date/sequence).
-- Keep captions readable as HTML, escaped below via PostgreSQL replace calls.
UPDATE fragment f
 SET page_id=m.destination_page_id,
     type='IMAGE', image_id=m.image_id,
     text=CASE WHEN trim(m.caption)='' THEN ''
       ELSE '<p>'||replace(replace(replace(m.caption,'&','&amp;'),'<','&lt;'),'>','&gt;')||'</p>' END,
     version=f.version+1
 FROM reviewed_0029 m WHERE f.id=m.source_id AND m.source_id<>84;
DO $verified$
DECLARE remaining bigint; cnt bigint;
BEGIN
 SELECT count(*) INTO remaining FROM fragment WHERE page_id IS NULL;
 IF remaining<>11 THEN RAISE EXCEPTION '0029 expected 11 remaining page-less, found %',remaining; END IF;
 SELECT count(*) INTO cnt FROM fragment f
 JOIN migration0029_rehearsal_receipt m ON f.id=m.source_id
 WHERE m.source_id<>84 AND f.type='IMAGE' AND f.image_id=m.image_id
 AND f.page_id=m.destination_page_id;
 IF cnt<>48 THEN RAISE EXCEPTION '0029 expected 48 converted IMAGE rows, found %',cnt; END IF;
 IF (SELECT count(*) FROM migration0029_legacy_image_archive)<>49 THEN
  RAISE EXCEPTION '0029 archived source count mismatch'; END IF;
END $verified$;
COMMIT;
SELECT 'PREP_PASS' AS gate, count(*) AS source_receipts FROM migration0029_rehearsal_receipt;

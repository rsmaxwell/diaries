-- 0029 Step 2. Read-only source and Page-context evidence for exactly the 49 reviewed IDs.
-- Values captured from 0029-49-review-manifest-20261125-174025.csv; do not edit without re-review.
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout='90s';
COPY (
WITH manifest(source_fragment_id, catalogue_id, source_html_md5, year, month, day, candidate_page_ids) AS (
 VALUES
 (84, 3, 'f8d05c41bd2932cf757a1bb0093dc887', 1828, 3, 20, '692'),
 (96, 4, 'ea6f050e163a6db36ed7cc5347dec453', 1828, 3, 31, '693'),
 (114, 5, '3ddd09f1c264a9366089588daf36427c', 1828, 4, 17, '694;695'),
 (115, 6, 'f98158f989daba1cb776b176cb525e9b', 1828, 4, 17, '694;695'),
 (116, 7, 'e46c98d54390d4ec24bca25d8106bc0f', 1828, 4, 17, '694;695'),
 (117, 8, 'b05424f59bddc780bbb2fb37e107aa29', 1828, 4, 17, '694;695'),
 (118, 9, '727d8becc9373c36715dd8464b52673d', 1828, 4, 17, '694;695'),
 (226, 10, '28325f1c9f3b3d9b92080a1f7c1accc5', 1828, 8, 1, '704'),
 (233, 11, '41ba63db77b05540e834dab028e049a4', 1828, 8, 7, '704'),
 (257, 12, 'd9a9c9f95ff7ce6b5e2285052bdacd3c', 1828, 8, 30, '707'),
 (258, 13, '2bb1cba383394729b662dbdb26387d5f', 1828, 8, 30, '707'),
 (259, 15, '4396e3e1881de6c049438ae165019be5', 1828, 8, 30, '707'),
 (260, 14, 'd40c9272230d848419d23ee842983519', 1828, 8, 30, '707'),
 (310, 16, '3b7c62f453ad74786d045b6012b72dca', 1828, 10, 17, '712'),
 (544, 72, '80755dfe6cf5255afd012ae7693d55bd', 1829, 6, 5, '737'),
 (545, 73, 'e4a8368faf47b38504e16273d25b1c06', 1829, 6, 5, '737'),
 (546, 74, '071fd7b214d8cec96ee165909ffb076c', 1829, 6, 5, '737'),
 (547, 75, '2eb57110a8a44ff1e570aa5993da1c93', 1829, 6, 5, '737'),
 (565, 75, '60dd00cd201403be413c7c5ca99a5af7', 1829, 6, 20, '741;742;743'),
 (575, 76, '2635c5dc4b42d9c498312de982523afd', 1829, 6, 26, '744;745'),
 (578, 17, 'af2a695910b0775cc923b084083c4f0e', 1829, 6, 27, '745'),
 (593, 22, '4a7929f8c404eec8b3716a35aeee0ebc', 1829, 7, 7, '752'),
 (594, 78, '03bbca67b111933f2110ed8f6e67b200', 1829, 7, 7, '752'),
 (595, 77, '8f2110e78df34b9c18c4b6a23910374c', 1829, 7, 7, '752'),
 (596, 19, '7a6fa2dd237dbde874b93e85a8f73f2f', 1829, 7, 7, '752'),
 (598, 18, '7c955bc3b85b2ae089cde13cba43c7db', 1829, 7, 8, '752;753'),
 (599, 21, '45e33a46485c68ef735f288d0c885974', 1829, 7, 8, '752;753'),
 (600, 20, 'ed7083ac2c5c914873da61511f6db37b', 1829, 7, 8, '752;753'),
 (606, 25, 'a397ecaa55a1c637b58d2575033d6f0c', 1829, 7, 11, '755'),
 (611, 24, 'cf8abe0cdbe80d440d44e738c0e81a69', 1829, 7, 14, '756;757'),
 (612, 23, '90b849836f2a5d4fea2a56de499c83c2', 1829, 7, 14, '756;757'),
 (613, 26, '86d9b6a5aaef160774d62cbd52b27fc3', 1829, 7, 14, '756;757'),
 (632, 27, 'd27f0163e1e312602334f17fe273223b', 1829, 7, 29, '761'),
 (633, 28, '273e4ed022332cc73b441bb23adb7194', 1829, 7, 29, '761'),
 (679, 80, '9e52191dab8c47463c9c0ad9fead32c7', 1829, 9, 5, '772'),
 (680, 2, '4f57177686fa57ba9f28e775b2a73ec9', 1829, 9, 5, '772'),
 (683, 30, 'c51ffd7538bf0479e84e0303cc948167', 1829, 9, 7, '772'),
 (684, 29, 'a2a4e87871e62d4311770d196e21cd2e', 1829, 9, 7, '772'),
 (720, 81, 'de8ad1a0a52b3d4d0df1f8235b6847a2', 1829, 10, 10, '778'),
 (722, 31, 'c8e6f71ce6d4ea21df6d5846ee2f12fa', 1829, 10, 11, '778'),
 (725, 32, '917bfa886745f1df2ffacfb1b826cc16', 1829, 10, 13, '779'),
 (739, 1, 'eebd6739c89e3be4b137aed5e0d00f37', 1829, 10, 26, '780'),
 (809, 35, 'ca739a596b216f6fe10330ce97b16e70', 1830, 1, 3, '788'),
 (980, 40, '5888c130ea685d3048484ef2fef92529', 1830, 6, 23, '827'),
 (1029, 41, '0e5f53a64d233460e4fc50602f54f890', 1830, 8, 10, '840'),
 (1030, 42, '9b04e5daa05b9ef2dc21a48c29ea1aef', 1830, 8, 10, '840'),
 (1043, 43, '0e98b62639be8f354dc176f8d4b7f6b0', 1830, 8, 22, '843'),
 (1182, 46, '82c4b6f92454c4dd50fa7e1ce3a81963', 1831, 1, 5, '874'),
 (1933, 71, '2c2116cee854b9d1507763aaf3ef23ef', 1834, 1, 7, '1066')
), source AS (
 SELECT m.*, f.text original_html, f.version live_version,
        f.page_id live_page_id, f.type live_type, f.image_id live_image_id,
        f.sequence live_sequence, md5(coalesce(f.text,'')) live_html_md5,
        i.relative_path catalogue_path,i.checksum catalogue_checksum
 FROM manifest m
 LEFT JOIN fragment f ON f.id=m.source_fragment_id
 LEFT JOIN image i ON i.id=m.catalogue_id
)

SELECT source_fragment_id, year,month,day,live_sequence,live_version,
       source_html_md5,live_html_md5,
       (source_html_md5=live_html_md5 AND live_page_id IS NULL AND live_type IS NULL AND live_image_id IS NULL) source_unchanged,
       catalogue_id,catalogue_path,catalogue_checksum,candidate_page_ids,
       original_html
FROM source ORDER BY source_fragment_id
) TO STDOUT WITH (FORMAT CSV, HEADER TRUE, FORCE_QUOTE *);
COMMIT;

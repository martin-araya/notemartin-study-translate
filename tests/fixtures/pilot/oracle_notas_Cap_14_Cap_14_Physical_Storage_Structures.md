---
schema_version: "1.0.0"
note_id: "cap-14-physical-storage-structures"
note_type: "chapter-digest"
title: "Capítulo 14 — Physical Storage Structures"
language: "es"
source:
  vendor: "Oracle"
  product: "Oracle AI Database"
  document: "Database Concepts"
  edition: "G42938-05"
  published: "April 20, 2026"
  source_file: "Cap_14_physical-storage-structures.pdf"
  pages: 21
  classification: "native_reliable"
  hash_sha256: "2aedf5fc6e26ba48"
coverage:
  regions_total: 28
  must_keep_total: 28
  must_keep_terminal: 28
  coverage_pct: 100
status: "draft"
reading_time_min: 35
tags:
  - "topic/oracle"
  - "topic/database-concepts"
  - "type/chapter-digest"
  - "type/concept"
  - "type/procedure"
  - "type/cheatsheet"
  - "type/glossary-term"
  - "domain/storage"
  - "oracle/physical-storage"
  - "oracle/data-file"
  - "oracle/temp-file"
  - "oracle/control-file"
  - "oracle/online-redo-log"
  - "oracle/archived-redo-log"
  - "oracle/oracle-managed-files"
  - "oracle/asm"
  - "oracle/asm-disk-group"
  - "oracle/asm-disk"
  - "oracle/asm-file"
  - "oracle/asm-extent"
  - "oracle/asm-allocation-unit"
  - "oracle/asm-instance"
  - "oracle/pmem-filestore"
  - "oracle/directly-mapped-buffer-cache"
  - "oracle/log-switch"
  - "oracle/multiplexed-redo-log"
related_concepts:
  - "[[term:physical-storage-structure]]"
  - "[[term:data-file]]"
  - "[[term:temp-file]]"
  - "[[term:permanent-data-file]]"
  - "[[term:temporary-data-file]]"
  - "[[term:online-data-file]]"
  - "[[term:offline-data-file]]"
  - "[[term:data-file-header]]"
  - "[[term:control-file]]"
  - "[[term:multiplexed-control-file]]"
  - "[[term:control-file-section]]"
  - "[[term:circular-reuse-record]]"
  - "[[term:noncircular-reuse-record]]"
  - "[[term:online-redo-log]]"
  - "[[term:redo-thread]]"
  - "[[term:log-switch]]"
  - "[[term:log-sequence-number]]"
  - "[[term:archived-redo-log]]"
  - "[[term:archivelog-mode]]"
  - "[[term:noarchivelog-mode]]"
  - "[[term:redo-record]]"
  - "[[term:oracle-managed-files]]"
  - "[[term:user-managed-files]]"
  - "[[term:oracle-asm]]"
  - "[[term:asm-disk]]"
  - "[[term:asm-disk-group]]"
  - "[[term:asm-file]]"
  - "[[term:asm-extent]]"
  - "[[term:asm-allocation-unit]]"
  - "[[term:asm-instance]]"
  - "[[term:oracle-pmem-filestore]]"
  - "[[term:directly-mapped-buffer-cache]]"
  - "[[term:fuse]]"
  - "[[term:redo-log-member]]"
  - "[[term:redo-log-group]]"
  - "[[term:multiplexed-redo-log]]"
  - "[[term:checkpoint-scn]]"
---

# Capítulo 14 — Physical Storage Structures

> **Procedencia:** Documento oficial *Database Concepts* (Oracle AI Database), edición **G42938-05**, publicado el **20 de abril de 2026**. Capítulo 14 del manual. **21 páginas en el PDF fuente**. Inicia **Part V — Oracle AI Database Storage Structures**. Texto en inglés; esta nota está redactada en español preservando nombres propios, identificadores y comandos SQL literales.

> **Resumen (L1):** Este capítulo cubre **Physical Storage Structures** en Oracle AI Database: introduction (independence de logical structures), **Oracle Managed Files vs User-Managed Files**, **Oracle Automatic Storage Management (Oracle ASM)** (disks, disk groups, files, extents, allocation units, instances), **Oracle Persistent Memory Filestore (PMEM Filestore)** (storage pyramid, FUSE, user interface), **Data Files** (permanent/temp, online/offline, structure), **Control Files** (use, multiple, structure), **Online Redo Log** (use, log threads, log switches, multiple copies), **Archived Redo Log Files**, y **Structure of Online Redo Log** (redo records).

---

## §1. Chapter Digest — visión completa del capítulo

### §1.1 Introduction to Physical Storage Structures

**Páginas 1–2.**

> **Regla preservada:** the **physical database structures de un Oracle database están viewable at el operating system level**. **One characteristic de un RDBMS está el independence de logical data structures** (tables, views, indexes) **de physical storage structures** (files). Because physical y logical structures están separate, **se puede manage physical storage de data 
# BONUSEDUCATION 2.0 — Android / Firebase

This branch is the rebuild of BONUSEDUCATION as a Firebase-only Android application.

## Goals

- Remove Google Sheets as the data source.
- Use Firebase Authentication + Firestore as the source of truth.
- Provide a teacher spreadsheet-like interface inside the Android app.
- Allow teachers to create, rename, reorder, hide and delete columns.
- Support normal columns and formula columns.
- Preserve student, teacher, group, ranking, points, transfer, commission, approval and transaction concepts from the existing bot.

## Planned Firestore model

```text
users/{userId}
groups/{groupId}
groups/{groupId}/columns/{columnId}
groups/{groupId}/students/{studentId}
transactions/{transactionId}
transferRequests/{requestId}
settings/system
```

## Spreadsheet column model

A column contains:

- `name`
- `type`: text, number, boolean, date, points, formula
- `order`
- `editable`
- `formula` (for formula columns)

Example formula:

```text
MASHQ + TEST * 2 + DIKTANT
```

The formula engine will later add `SUM`, `AVG`, `MIN`, `MAX`, `ROUND`, `IF`, dependency validation and circular-reference detection.

## Security

Sensitive point mutations should be performed through trusted backend/Cloud Functions rather than trusting client-side writes. Firestore Security Rules will enforce role and group access.

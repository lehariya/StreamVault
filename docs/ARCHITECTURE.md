# Architecture and data model

- User 1-to-many Subscription: subscription history is retained over time.
- Plan 1-to-many Subscription: each subscription points to a plan.
- User 1-to-many DownloadRecord: a user's audit history.
- Video 1-to-many DownloadRecord: each attempt references the requested video.
- User 1-to-many RegisteredDevice: optional allow-list of browser/device IDs.

Download authorization is evaluated by Flask on each actual download request. The frontend authorization call is a user-friendly preflight only. DownloadRecord uses a unique idempotency key. Pending records reserve quota until the transfer is closed or reconciled.

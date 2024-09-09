from sqlalchemy import Table, Column, Integer, String, ForeignKey, Enum
from .database import metadata
import enum
from sqlalchemy.dialects.postgresql import JSONB


class BodyType(enum.Enum):
    raw = "raw"
    form = "form"

collections = Table(
    "collections",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String),
)

requests = Table(
    "requests",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("url", String),
    Column("method", String),
    Column("body", JSONB),
    Column("bodytype", Enum(BodyType)),
    Column("collection_id", Integer, ForeignKey("collections.id")),
)

params = Table(
    "params",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("key", String),
    Column("value", String),
    Column("request_id", Integer, ForeignKey("requests.id")),
)

response = Table(
    "response",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("body", JSONB),
    Column("status_code", Integer),
    Column("request_id", Integer, ForeignKey("requests.id"))
)
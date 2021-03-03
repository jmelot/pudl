"""Metadata data classes."""
import copy
import datetime
import uuid
from typing import (Any, Callable, Dict, Iterable, List, Literal, Optional,
                    Tuple, Type, Union)

import pandas as pd
import pydantic
import sqlalchemy as sa

from .constants import (CONTRIBUTORS, CONTRIBUTORS_BY_SOURCE, FIELD_DTYPES,
                        FIELD_DTYPES_SQL, KEYWORDS_BY_SOURCE, LICENSES,
                        PERIODS, SOURCES)
from .fields import FIELDS
from .helpers import (expand_periodic_column_names, groupby_aggregate,
                      has_duplicate_basenames, most_and_more_frequent,
                      split_period)
from .resources import FOREIGN_KEYS, RESOURCES

# ---- Base ---- #


class Base(pydantic.BaseModel):
    """
    Custom Pydantic base class.

    It overrides :meth:`fields` and :meth:`schema` to allow properties with those names.
    To use them in a class, use an underscore prefix and an alias.

    Examples:
        >>> class Class(Base):
        ...     fields_: List[str] = pydantic.Field(alias="fields")
        >>> m = Class(fields=['x'])
        >>> m
        Class(fields=['x'])
        >>> m.fields
        ['x']
        >>> m.fields = ['y']
        >>> m.dict()
        {'fields': ['y']}
    """

    class Config:
        """Custom Pydantic configuration."""

        validate_all: bool = True
        validate_assignment: bool = True
        extra: str = 'forbid'

    def dict(self, *args, by_alias=True, **kwargs) -> dict:  # noqa: A003
        """Return as a dictionary."""
        return super().dict(*args, by_alias=by_alias, **kwargs)

    def json(self, *args, by_alias=True, **kwargs) -> str:
        """Return as JSON."""
        return super().json(*args, by_alias=by_alias, **kwargs)

    def __getattribute__(self, name: str) -> Any:
        """Get attribute."""
        if name in ("fields", "schema") and f"{name}_" in self.__dict__:
            name = f"{name}_"
        return super().__getattribute__(name)

    def __setattr__(self, name, value) -> None:
        """Set attribute."""
        if name in ("fields", "schema") and f"{name}_" in self.__dict__:
            name = f"{name}_"
        super().__setattr__(name, value)

    def __repr_args__(self) -> List[Tuple[str, Any]]:
        """Returns the attributes to show in __str__, __repr__, and __pretty__."""
        return [
            (a[:-1] if a in ("fields_", "schema_") else a, v)
            for a, v in self.__dict__.items()
        ]


# ---- Class attribute types ---- #


String = pydantic.constr(min_length=1, strict=True)
"""
Non-empty :class:`str` (anything except "").
"""

Bool = pydantic.StrictBool
"""
Any :class:`bool` (`True` or `False`).
"""

Float = pydantic.confloat(ge=0, strict=True)
"""
Positive :class:`float`.
"""


def StrictList(item_type: Type = Any) -> pydantic.ConstrainedList:  # noqa: N802
    """
    Non-empty :class:`list`.

    Allows :class:`list`, :class:`tuple`, :class:`set`, :class:`frozenset`,
    :class:`collections.deque`, or generators and casts to a :class:`list`.
    """
    return pydantic.conlist(item_type=item_type, min_items=1)


# ---- Class attribute validators ---- #


def _check_unique(value: list = None) -> Optional[list]:
    """Check that input list has unique values."""
    if value:
        for i in range(len(value)):
            if value[i] in value[:i]:
                raise ValueError(f"contains duplicate {value[i]}")
    return value


def _stringify(value: Any = None) -> Optional[str]:
    """Convert input to string."""
    if value:
        return str(value)
    return value


def _validator(*names, fn: Callable) -> Callable:
    """
    Construct reusable Pydantic validator.

    Args:
        names: Names of attributes to validate.
        fn: Validation function (see :meth:`pydantic.validator`).

    Examples:
        >>> class Class(Base):
        ...     x: int = None
        ...     y: list = None
        ...     _stringify = _validator("x", fn=_stringify)
        ...     _check_unique = _validator("y", fn=_check_unique)
        >>> Class(x=1).x
        '1'
        >>> Class(y=[0, 0])
        Traceback (most recent call last):
          ...
        ValidationError: ...
    """
    return pydantic.validator(*names, allow_reuse=True)(fn)


# ---- Classes: Field ---- #


class FieldConstraints(Base):
    """
    Field constraints (`resource.schema.fields[...].constraints`).

    See https://specs.frictionlessdata.io/table-schema/#constraints.
    """

    required: Bool = False
    unique: Bool = False
    enum: StrictList(Any) = None

    _check_unique = _validator("enum", fn=_check_unique)


class FieldHarvest(Base):
    """Field harvest parameters (`resource.schema.fields[...].harvest`)."""

    # NOTE: Callables with defaults must use pydantic.Field() to not bind to self
    aggregate: Callable[[pd.Series], pd.Series] = pydantic.Field(
        default=lambda x: most_and_more_frequent(x, min_frequency=0.7)
    )
    """Computes a single value from all field values in a group."""

    tolerance: Float = 0.0
    """Fraction of invalid groups above which result is considered invalid."""


class Field(Base):
    """
    Field (`resource.schema.fields[...]`).

    See https://specs.frictionlessdata.io/table-schema/#field-descriptors.

    Examples:
        >>> field = Field(name='x', type='string', constraints={'enum': ['x', 'y']})
        >>> field.dtype
        CategoricalDtype(categories=['x', 'y'], ordered=False)
        >>> field.to_sql()
        Column('x', Enum('x', 'y'), table=None)
        >>> field = Field.from_id('utility_id_eia')
        >>> field.name
        'utility_id_eia'
    """

    name: String
    type: String  # noqa: A003
    format: Literal["default"] = "default"  # noqa: A003
    description: String = None
    constraints: FieldConstraints = {}
    harvest: FieldHarvest = {}

    @pydantic.validator("type")
    # NOTE: Could be replaced with `type: Literal[...]`
    def _check_type_supported(cls, value):  # noqa: N805
        if value not in FIELD_DTYPES:
            raise ValueError(f"must be one of {list(FIELD_DTYPES.keys())}")
        return value

    @pydantic.validator("constraints")
    def _check_enum_type(cls, value, values):  # noqa: N805
        if value.enum and "type" in values:
            if values["type"] != "string":
                raise ValueError("Non-string enum type is not supported")
            for x in value.enum:
                if not isinstance(x, str):
                    raise ValueError(f"Enum value '{x}' is not {values['type']}")
        return value

    @classmethod
    def from_id(cls, x: str) -> 'Field':
        """Construct from PUDL identifier (`Field.name`)."""
        return cls(name=x, **FIELDS[x])

    @property
    def dtype(self) -> Union[str, pd.CategoricalDtype]:
        """Pandas data type."""
        if self.constraints.enum:
            return pd.CategoricalDtype(self.constraints.enum)
        return FIELD_DTYPES[self.type]

    @property
    def dtype_sql(self) -> sa.sql.visitors.VisitableType:
        """SQLAlchemy data type."""  # noqa: D403
        if self.constraints.enum:
            return sa.Enum(*self.constraints.enum, create_constraint=True)
        return FIELD_DTYPES_SQL[self.type]

    def to_sql(self) -> sa.Column:
        """Return equivalent SQL column."""
        return sa.Column(
            self.name,
            self.dtype_sql,
            nullable=not self.constraints.required,
            unique=self.constraints.unique,
            comment=self.description
        )


# ---- Classes: Resource ---- #


class ForeignKeyReference(Base):
    """
    Foreign key reference (`resource.schema.foreignKeys[...].reference`).

    See https://specs.frictionlessdata.io/table-schema/#foreign-keys.
    """

    resource: String
    fields_: StrictList(String) = pydantic.Field(alias="fields")

    _check_unique = _validator("fields_", fn=_check_unique)


class ForeignKey(Base):
    """
    Foreign key (`resource.schema.foreignKeys[...]`).

    See https://specs.frictionlessdata.io/table-schema/#foreign-keys.
    """

    fields_: StrictList(String) = pydantic.Field(alias="fields")
    reference: ForeignKeyReference

    _check_unique = _validator("fields_", fn=_check_unique)

    @pydantic.validator("reference")
    def _check_fields_equal_length(cls, value, values):  # noqa: N805
        if "fields_" in values:
            if len(value.fields) != len(values["fields_"]):
                raise ValueError("fields and reference.fields are not equal length")
        return value

    def to_sql(self) -> sa.ForeignKeyConstraint:
        """Return equivalent SQL Foreign Key."""
        return sa.ForeignKeyConstraint(
            self.fields,
            [f"{self.reference.resource}.{field}" for field in self.reference.fields]
        )


class Schema(Base):
    """
    Table schema (`resource.schema`).

    See https://specs.frictionlessdata.io/table-schema.
    """

    fields_: StrictList(Field) = pydantic.Field(alias="fields")
    missingValues: List[pydantic.StrictStr] = [""]  # noqa: N815
    primaryKey: StrictList(String) = None  # noqa: N815
    foreignKeys: List[ForeignKey] = []  # noqa: N815

    _check_unique = _validator(
        "missingValues", "primaryKey", "foreignKeys", fn=_check_unique
    )

    @pydantic.validator("fields_")
    def _check_field_names_unique(cls, value):  # noqa: N805
        _check_unique([f.name for f in value])
        return value

    @pydantic.validator("primaryKey")
    def _check_primary_key_in_fields(cls, value, values):  # noqa: N805
        if value is not None and "fields_" in values:
            names = [f.name for f in values['fields_']]
            missing = [x for x in value if x not in names]
            if missing:
                raise ValueError(f"names {missing} missing from fields")
        return value

    @pydantic.validator("foreignKeys", each_item=True)
    def _check_foreign_key_in_fields(cls, value, values):  # noqa: N805
        if value and "fields_" in values:
            names = [f.name for f in values['fields_']]
            missing = [x for x in value.fields if x not in names]
            if missing:
                raise ValueError(f"names {missing} missing from fields")
        return value


class Dialect(Base):
    """
    CSV dialect (`resource.dialect`).

    See https://specs.frictionlessdata.io/csv-dialect.
    """

    delimiter: String = ","
    header: Bool = True
    quoteChar: String = "\""  # noqa: N815
    doubleQuote: Bool = True  # noqa: N815
    lineTerminator: String = "\r\n"  # noqa: N815
    skipInitialSpace: Bool = True  # noqa: N815
    caseSensitiveHeader: Bool = False  # noqa: N815


class License(Base):
    """
    Data license (`package|resource.licenses[...]`).

    See https://specs.frictionlessdata.io/data-package/#licenses.
    """

    name: String
    title: String
    path: pydantic.AnyHttpUrl

    _stringify = _validator("path", fn=_stringify)

    @classmethod
    def from_id(cls, x: str) -> "License":
        """Construct from PUDL identifier."""
        return cls(**LICENSES[x])


class Source(Base):
    """
    Data source (`package|resource.sources[...]`).

    See https://specs.frictionlessdata.io/data-package/#sources.
    """

    title: String
    path: pydantic.AnyHttpUrl
    email: pydantic.EmailStr = None

    _stringify = _validator("path", "email", fn=_stringify)

    @classmethod
    def from_id(cls, x: str) -> "Source":
        """Construct from PUDL identifier."""
        return cls(**SOURCES[x])


class Contributor(Base):
    """
    Data contributor (`package.contributors[...]`).

    See https://specs.frictionlessdata.io/data-package/#contributors.
    """

    title: String
    path: pydantic.AnyHttpUrl = None
    email: pydantic.EmailStr = None
    role: Literal[
        "author", "contributor", "maintainer", "publisher", "wrangler"
    ] = "contributor"
    organization: String = None

    _stringify = _validator("path", "email", fn=_stringify)

    @classmethod
    def from_id(cls, x: str) -> "Contributor":
        """Construct from PUDL identifier."""
        return cls(**CONTRIBUTORS[x])


class ResourceHarvest(Base):
    """Resource harvest parameters (`resource.harvest`)."""

    harvest: Bool = False
    """
    Whether to harvest from dataframes based on field names.

    If `False`, the dataframe with the same name is used
    and the process is limited to dropping unwanted fields.
    """

    tolerance: Float = 0.0
    """Fraction of invalid fields above which result is considerd invalid."""


class Resource(Base):
    """
    Tabular data resource (`package.resources[...]`).

    See https://specs.frictionlessdata.io/tabular-data-resource.

    Examples:
        A simple example illustrates the conversion to SQLAlchemy objects.

        >>> fields = [{'name': 'x', 'type': 'year'}, {'name': 'y', 'type': 'string'}]
        >>> fkeys = [{'fields': ['x', 'y'], 'reference': {'resource': 'b', 'fields': ['x', 'y']}}]
        >>> schema = {'fields': fields, 'primaryKey': ['x'], 'foreignKeys': fkeys}
        >>> resource = Resource(name='a', schema=schema)
        >>> table = resource.to_sql()
        >>> table.columns.x
        Column('x', Integer(), ForeignKey('b.x'), table=<a>, primary_key=True, nullable=False)
        >>> table.columns.y
        Column('y', Text(), ForeignKey('b.y'), table=<a>)

        To illustrate harvesting operations,
        say we have a resource with two fields - a primary key (`id`) and a data field -
        which we want to harvest from two different dataframes.

        >>> from pudl.metadata.helpers import unique, as_dict
        >>> fields = [
        ...     {'name': 'id', 'type': 'integer'},
        ...     {'name': 'x', 'type': 'integer', 'harvest': {'aggregate': unique, 'tolerance': 0.25}}
        ... ]
        >>> resource = Resource(**{
        ...     'name': 'A',
        ...     'harvest': {'harvest': True},
        ...     'schema': {'fields': fields, 'primaryKey': ['id']}
        ... })
        >>> dfs = {
        ...     'A': pd.DataFrame({'id': [1, 1, 2, 2], 'x': [1, 1, 2, 2]}),
        ...     'B': pd.DataFrame({'id': [2, 3, 3], 'x': [3, 4, 4]})
        ... }

        Skip aggregation to access all the rows concatenated from the input dataframes.
        The names of the input dataframes are used as the index.

        >>> df, _ = resource.harvest_dfs(dfs, aggregate=False)
        >>> df
            id  x
        df
        A    1  1
        A    1  1
        A    2  2
        A    2  2
        B    2  3
        B    3  4
        B    3  4

        Field names and data types are enforced.

        >>> resource.dtypes == df.dtypes.apply(str).to_dict()
        True

        Alternatively, aggregate by primary key
        (the default when :attr:`harvest`. `harvest=True`)
        and report aggregation errors.

        >>> df, report = resource.harvest_dfs(dfs)
        >>> df
               x
        id
        1      1
        2   <NA>
        3      4
        >>> report['stats']
        {'all': 2, 'invalid': 1, 'tolerance': 0.0, 'actual': 0.5}
        >>> report['fields']['x']['stats']
        {'all': 3, 'invalid': 1, 'tolerance': 0.25, 'actual': 0.33...}
        >>> report['fields']['x']['errors']
        id
        2    Not unique.
        Name: x, dtype: object

        Customize the error values in the error report.

        >>> errorfunc = lambda x, e: as_dict(x)
        >>> df, report = resource.harvest_dfs(dfs, errorfunc=errorfunc, raise_errors=False)
        >>> report['fields']['x']['errors']
        id
        2    {'A': [2, 2], 'B': [3]}
        Name: x, dtype: object

        Limit harvesting to the input dataframe of the same name
        by setting :attr:`harvest`. `harvest=False`.

        >>> resource.harvest.harvest = False
        >>> df, _ = resource.harvest_dfs(dfs, raise_errors=False)
        >>> df
            id  x
        df
        A    1  1
        A    1  1
        A    2  2
        A    2  2

        Harvesting can also handle conversion to longer time periods.
        Period harvesting requires primary key fields with a `datetime` data type,
        so `year` fields (with `Int64` data type) are not currently supported.

        >>> fields = [{'name': 'report_year', 'type': 'date'}]
        >>> resource = Resource(**{
        ...     'name': 'table',
        ...     'schema': {'fields': fields, 'primaryKey': ['report_year']}
        ... })
        >>> df = pd.DataFrame({'report_date': ['2000-02-02', '2000-03-03']})
        >>> resource.format_df(df)
          report_year
        0  2000-01-01
        1  2000-01-01
    """

    name: String
    path: pydantic.FilePath = None
    title: String = None
    description: String = None
    harvest: ResourceHarvest = {}
    profile: Literal["tabular-data-resource"] = "tabular-data-resource"
    encoding: Literal["utf-8"] = "utf-8"
    mediatype: Literal["text/csv"] = "text/csv"
    format: Literal["csv"] = "csv"  # noqa: A003
    dialect: Dialect = {}
    schema_: Schema = pydantic.Field(alias='schema')
    contributors: List[Contributor] = []
    licenses: List[License] = []
    sources: List[Source] = []
    keywords: List[String] = []

    _stringify = _validator("path", fn=_stringify)
    _check_unique = _validator(
        "contributors", "keywords", "licenses", "sources", fn=_check_unique
    )

    @pydantic.validator("schema_")
    def _check_field_basenames_unique(cls, value):  # noqa: N805
        if has_duplicate_basenames([f.name for f in value.fields]):
            raise ValueError("Field names contain duplicate basenames")
        return value

    @classmethod
    def from_id(cls, x: str) -> "Resource":
        """
        Construct from PUDL identifier (`resource.name`).

        * `schema.fields`

          * Field names are expanded (:meth:`Field.from_id`).
          * Field descriptors are expanded by name
            (e.g. `{'name': 'x', ...}` to `Field.from_id('x')`)
            and updated with custom properties (e.g. `{..., 'description': '...'}`).

        * `sources`

          * Source ids are expanded (:meth:`Source.from_id`).
          * Source descriptors are used as is.

        * `contributors`: Contributor ids are fetched by source ids,
          then expanded (:meth:`Contributor.from_id`).
        * `keywords`: Keywords are fetched by source ids.
        * `schema.foreignKeys`: Foreign keys are fetched by resource name.
        """
        obj = copy.deepcopy(RESOURCES[x])
        schema = obj["schema"]
        # Expand fields
        if "fields" in schema:
            fields = []
            for value in schema["fields"]:
                if isinstance(value, str):
                    # Lookup field by name
                    fields.append(Field.from_id(value))
                else:
                    # Lookup field by name and update with custom metadata
                    fields.append(Field.from_id(value["name"]).copy(update=value))
            schema["fields"] = fields
        # Expand sources
        sources = obj.get("sources", [])
        obj["sources"] = [
            Source.from_id(value) if isinstance(value, str) else value
            for value in sources
        ]
        # Lookup and insert contributors
        if "contributors" in schema:
            raise ValueError("Resource metadata contains explicit contributors")
        cids = []
        for source in sources:
            cids.extend(CONTRIBUTORS_BY_SOURCE.get(source, []))
        obj["contributors"] = [Contributor.from_id(cid) for cid in set(cids)]
        # Lookup and insert keywords
        if "keywords" in schema:
            raise ValueError("Resource metadata contains explicit keywords")
        keywords = []
        for source in sources:
            keywords.extend(KEYWORDS_BY_SOURCE.get(source, []))
        obj["keywords"] = list(set(keywords))
        # Insert foreign keys
        if "foreignKeys" in schema:
            raise ValueError("Resource metadata contains explicit foreign keys")
        schema["foreignKeys"] = FOREIGN_KEYS.get(x, [])
        # Delete foreign key rules
        if "foreignKeyRules" in schema:
            del schema["foreignKeyRules"]
        return cls(name=x, **obj)

    def to_sql(self, metadata: sa.MetaData = None) -> sa.Table:
        """Return equivalent SQL Table."""
        if metadata is None:
            metadata = sa.MetaData()
        columns = [f.to_sql() for f in self.schema.fields]
        constraints = []
        if self.schema.primaryKey:
            constraints.append(sa.PrimaryKeyConstraint(*self.schema.primaryKey))
        for key in self.schema.foreignKeys:
            constraints.append(key.to_sql())
        return sa.Table(self.name, metadata, *columns, *constraints)

    @property
    def dtypes(self) -> Dict[str, Union[str, pd.CategoricalDtype]]:
        """Pandas data type of each field by field name."""
        return {f.name: f.dtype for f in self.schema.fields}

    def match_primary_key(self, names: Iterable[str]) -> Optional[Dict[str, str]]:
        """
        Match primary key fields to input field names.

        An exact match is required,
        except for periodic names which also match a basename with a smaller period.

        Args:
            names: Field names.

        Raises:
            ValueError: Field names contain duplicate basenames.

        Returns:
            The name in `names` matching each primary key field (dict),
            or `None` if not all primary key fields have a match.
        """
        if has_duplicate_basenames(names):
            raise ValueError("Field names contain duplicate basenames")
        key = self.schema.primaryKey or []
        match = {}
        for k in key:
            for name in expand_periodic_column_names([k]):
                if name in names:
                    match[name] = k
                    break
        return match if len(match) == len(key) else None

    def format_df(self, df: pd.DataFrame = None) -> pd.DataFrame:
        """
        Format a dataframe.

        Args:
            df: Dataframe to format.

        Raises:
            NotImplementedError: A primary key is required for formatting.

        Returns:
            Dataframe with column names and data types matching the resource fields.
            Periodic primary key fields are snapped to the start of the desired period.
            If the primary key fields could not be matched to columns in `df`
            (:meth:`match_primary_key`) or if `df=None`, an empty dataframe is returned.
        """
        if df is None:
            return pd.DataFrame({n: pd.Series(dtype=d) for n, d in self.dtypes.items()})
        # TODO: Check whether and when this is still true
        if not self.schema.primaryKey:
            raise NotImplementedError("A primary key is required for harvesting")
        match = self.match_primary_key(df.columns)
        if match is None:
            return self.format_df()
        dtypes = self.dtypes
        df = (
            df.copy()
            # Rename periodic key columns to the requested period
            .rename(columns=match, copy=False)
            # Reorder columns and insert missing columns
            .reindex(columns=dtypes.keys(), copy=False)
            # Coerce columns to correct data type
            .astype(dtypes, copy=False)
        )
        # Convert periodic key columns to the requested period
        for df_key, key in match.items():
            _, period = split_period(key)
            if period and df_key != key:
                df[key] = PERIODS[period](df[key])
        return df

    def aggregate_df(
        self, df: pd.DataFrame, raise_errors: bool = False, errorfunc: Callable = None
    ) -> Tuple[pd.DataFrame, dict]:
        """
        Aggregate dataframe by primary key.

        The dataframe is grouped by primary key fields
        and aggregated with the aggregate function of each field
        (:attr:`schema_`. `fields[*].harvest.aggregate`).

        The report is formatted as follows:

        * `valid` (bool): Whether resouce is valid.
        * `stats` (dict): Error statistics for resource fields.
        * `fields` (dict):

          * `<field_name>` (str)

            * `valid` (bool): Whether field is valid.
            * `stats` (dict): Error statistics for field groups.
            * `errors` (:class:`pandas.Series`): Error values indexed by primary key.

          * ...

        Each `stats` (dict) contains the following:

        * `all` (int): Number of entities (field or field group).
        * `invalid` (int): Invalid number of entities.
        * `tolerance` (float): Fraction of invalid entities below which
          parent entity is considered valid.
        * `actual` (float): Actual fraction of invalid entities.

        Args:
            df: Dataframe to aggregate. It is assumed to have column names and
              data types matching the resource fields.
            raise_errors: Whether to stop at the first aggregation error.
            errorfunc: A function with signature `f(x, e) -> Any`,
              where `x` are the original field values as a :class:`pandas.Series`
              and `e` is the original error.
              If provided, the returned value is reported instead of `e`.

        Raises:
            NotImplementedError: A primary key is required for aggregating.

        Returns:
            The aggregated dataframe indexed by primary key fields,
            and an aggregation report (descripted above)
            that includes all aggregation errors and whether the result
            meets the resource's and fields' tolerance.
        """
        if not self.schema.primaryKey:
            raise NotImplementedError("A primary key is required for aggregating")
        aggfuncs = {
            f.name: f.harvest.aggregate
            for f in self.schema.fields
            if f.name not in self.schema.primaryKey
        }
        df, report = groupby_aggregate(
            df,
            by=self.schema.primaryKey,
            aggfuncs=aggfuncs,
            errors="raise" if raise_errors else "report",
            errorfunc=errorfunc,
        )
        report = self._build_aggregation_report(df, report)
        return df, report

    def _build_aggregation_report(self, df: pd.DataFrame, errors: dict) -> dict:
        """
        Build report from aggregation errors.

        Args:
            df: Harvested dataframe (see :meth:`harvest_dfs`).
            errors: Aggregation errors (see :func:`groupby_aggregate`).

        Returns:
            Aggregation report, as described in :meth:`aggregate_df`.
        """
        nrows, ncols = df.reset_index().shape
        freports = {}
        for field in self.schema.fields:
            if field.name in errors:
                nerrors = errors[field.name].size
            else:
                nerrors = 0
            stats = {
                "all": nrows,
                "invalid": nerrors,
                "tolerance": field.harvest.tolerance,
                "actual": nerrors / nrows if nrows else 0,
            }
            freports[field.name] = {
                "valid": stats["actual"] <= stats["tolerance"],
                "stats": stats,
                "errors": errors.get(field.name, None),
            }
        nerrors = sum([not f["valid"] for f in freports.values()])
        stats = {
            "all": ncols,
            "invalid": nerrors,
            "tolerance": self.harvest.tolerance,
            "actual": nerrors / ncols,
        }
        return {
            "valid": stats["actual"] <= stats["tolerance"],
            "stats": stats,
            "fields": freports,
        }

    def harvest_dfs(
        self, dfs: Dict[str, pd.DataFrame], aggregate: bool = None, **kwargs: Any
    ) -> Tuple[pd.DataFrame, dict]:
        """
        Harvest from named dataframes.

        For standard resources (:attr:`harvest`. `harvest=False`),
        the columns matching all primary key fields and any data fields
        are extracted from the input dataframe of the same name.

        For harvested resources (:attr:`harvest`. `harvest=True`),
        the columns matching all primary key fields and any data fields
        are extracted from each compatible input dataframe,
        and concatenated into a single dataframe.

        In either case, periodic key fields (e.g. 'report_month') are matched to any
        column of the same name with an equal or smaller period (e.g. 'report_day')
        and snapped to the start of the desired period.

        If `aggregate=False`, rows are indexed by the name of the input dataframe.
        If `aggregate=True`, rows are indexed by primary key fields.

        Args:
            dfs: Dataframes to harvest.
            aggregate: Whether to aggregate the harvested rows by their primary key.
              By default, this is `True` if `self.harvest.harvest=True`
              and `False` otherwise.
            kwargs: Optional arguments to :meth:`aggregate_df`.

        Returns:
            A dataframe harvested from the dataframes,
            with column names and data types matching the resource fields,
            alongside an aggregation report.
        """
        if aggregate is None:
            aggregate = self.harvest.harvest
        if self.harvest.harvest:
            # Harvest resource from all inputs where all primary key fields are present
            samples = {}
            for name, df in dfs.items():
                samples[name] = self.format_df(df)
                # Pass input names to aggregate via the index
                samples[name].index = pd.Index([name] * len(samples[name]), name="df")
            df = pd.concat(samples.values())
        elif self.name in dfs:
            # Subset resource from input of same name
            df = self.format_df(dfs[self.name])
            # Pass input names to aggregate via the index
            df.index = pd.Index([self.name] * df.shape[0], name="df")
        else:
            return self.format_df(), {}
        if aggregate:
            return self.aggregate_df(df, **kwargs)
        return df, {}

# ---- Package ---- #


class Package(Base):
    """
    Tabular data package.

    See https://specs.frictionlessdata.io/data-package.

    Examples:
        Foreign keys between resources are checked for completeness and consistency.

        >>> fields = [{'name': 'x', 'type': 'year'}, {'name': 'y', 'type': 'string'}]
        >>> fkey = {'fields': ['x', 'y'], 'reference': {'resource': 'b', 'fields': ['x', 'y']}}
        >>> schema = {'fields': fields, 'primaryKey': ['x'], 'foreignKeys': [fkey]}
        >>> a = Resource(name='a', schema=schema)
        >>> b = Resource(name='b', schema=Schema(fields=fields, primaryKey=['x']))
        >>> Package(name='ab', resources=[a, b])
        Traceback (most recent call last):
        ValidationError: ...
        >>> b.schema.primaryKey = ['x', 'y']
        >>> package = Package(name='ab', resources=[a, b])

        SQL Alchemy can sort tables, based on foreign keys,
        in the order in which they need to be loaded into a database.

        >>> metadata = package.to_sql()
        >>> [table.name for table in metadata.sorted_tables]
        ['b', 'a']
    """

    name: String
    id: pydantic.UUID4 = uuid.uuid4()  # noqa: A003
    profile: Literal["tabular-data-package"] = "tabular-data-package"
    title: String = None
    description: String = None
    keywords: List[String] = []
    homepage: pydantic.HttpUrl = "https://catalyst.coop/pudl"
    created: datetime.datetime = datetime.datetime.utcnow()
    contributors: List[Contributor] = []
    sources: List[Source] = []
    licenses: List[License] = []
    resources: StrictList(Resource)

    _stringify = _validator("id", "homepage", fn=_stringify)

    @pydantic.validator("created")
    def _stringify_datetime(cls, value):  # noqa: N805
        return value.strftime(format="%Y-%m-%dT%H:%M:%SZ")

    @pydantic.validator("resources")
    def _check_foreign_keys(cls, value):
        rnames = [resource.name for resource in value]
        errors = []
        for resource in value:
            for foreignKey in resource.schema.foreignKeys:
                rname = foreignKey.reference.resource
                tag = f"\t* [{resource.name} -> {rname}]"
                if rname not in rnames:
                    errors.append(f"{tag}: Reference not found")
                    continue
                reference = value[rnames.index(rname)]
                if not reference.schema.primaryKey:
                    errors.append(f"{tag}: Reference missing primary key")
                    continue
                missing = [
                    x for x in foreignKey.reference.fields
                    if x not in reference.schema.primaryKey
                ]
                if missing:
                    errors.append(f"{tag}: Reference primary key missing {missing}")
        if errors:
            raise ValueError("Foreign keys\n" + '\n'.join(errors))
        return value

    def to_sql(self) -> sa.MetaData:
        """Return equivalent SQL MetaData."""
        metadata = sa.MetaData()
        for resource in self.resources:
            _ = resource.to_sql(metadata)
        return metadata

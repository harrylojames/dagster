import pytest
from dagster import (
    AssetKey,
    AssetOut,
    FilesystemIOManager,
    IOManager,
    SourceAsset,
    asset,
    materialize,
    multi_asset,
)
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.types.dagster_type import DagsterTypeKind


class TestingIOManager(IOManager):
    def handle_output(self, context, obj):
        return None

    def load_input(self, context):
        # we should be bypassing the IO Manager, so fail if try to load an input
        assert False


def test_single_asset_deps_via_assets_definition():
    @asset
    def asset_1():
        return None

    @asset(deps=[asset_1])
    def asset_2():
        return None

    assert len(asset_2.input_names) == 1
    assert asset_2.op.ins["asset_1"].dagster_type.is_nothing

    res = materialize([asset_1, asset_2], resources={"io_manager": TestingIOManager()})

    assert res.success


def test_single_asset_deps_via_string():
    @asset
    def asset_1():
        return None

    @asset(deps=["asset_1"])
    def asset_2():
        return None

    assert len(asset_2.input_names) == 1
    assert asset_2.op.ins["asset_1"].dagster_type.is_nothing

    res = materialize([asset_1, asset_2], resources={"io_manager": TestingIOManager()})

    assert res.success


def test_single_asset_deps_via_asset_key():
    @asset
    def asset_1():
        return None

    @asset(deps=[AssetKey("asset_1")])
    def asset_2():
        return None

    assert len(asset_2.input_names) == 1
    assert asset_2.op.ins["asset_1"].dagster_type.is_nothing

    res = materialize([asset_1, asset_2], resources={"io_manager": TestingIOManager()})
    assert res.success


def test_single_asset_deps_via_mixed_types():
    @asset
    def via_definition():
        return None

    @asset
    def via_string():
        return None

    @asset
    def via_asset_key():
        return None

    @asset(deps=[via_definition, "via_string", AssetKey("via_asset_key")])
    def downstream():
        return None

    assert len(downstream.input_names) == 3
    assert downstream.op.ins["via_definition"].dagster_type.is_nothing
    assert downstream.op.ins["via_string"].dagster_type.is_nothing
    assert downstream.op.ins["via_asset_key"].dagster_type.is_nothing

    res = materialize(
        [via_definition, via_string, via_asset_key, downstream],
        resources={"io_manager": TestingIOManager()},
    )
    assert res.success


def test_multi_asset_deps_via_string():
    @multi_asset(
        outs={
            "asset_1": AssetOut(),
            "asset_2": AssetOut(),
        }
    )
    def a_multi_asset():
        return None, None

    @asset(deps=["asset_1"])
    def depends_on_one_sub_asset():
        return None

    assert len(depends_on_one_sub_asset.input_names) == 1
    assert depends_on_one_sub_asset.op.ins["asset_1"].dagster_type.is_nothing

    @asset(deps=["asset_1", "asset_2"])
    def depends_on_both_sub_assets():
        return None

    assert len(depends_on_both_sub_assets.input_names) == 2
    assert depends_on_both_sub_assets.op.ins["asset_1"].dagster_type.is_nothing
    assert depends_on_both_sub_assets.op.ins["asset_2"].dagster_type.is_nothing

    res = materialize(
        [a_multi_asset, depends_on_one_sub_asset, depends_on_both_sub_assets],
        resources={"io_manager": TestingIOManager()},
    )
    assert res.success


def test_multi_asset_deps_via_key():
    @multi_asset(
        outs={
            "asset_1": AssetOut(),
            "asset_2": AssetOut(),
        }
    )
    def a_multi_asset():
        return None, None

    @asset(deps=[AssetKey("asset_1")])
    def depends_on_one_sub_asset():
        return None

    assert len(depends_on_one_sub_asset.input_names) == 1
    assert depends_on_one_sub_asset.op.ins["asset_1"].dagster_type.is_nothing

    @asset(deps=[AssetKey("asset_1"), AssetKey("asset_2")])
    def depends_on_both_sub_assets():
        return None

    assert len(depends_on_both_sub_assets.input_names) == 2
    assert depends_on_both_sub_assets.op.ins["asset_1"].dagster_type.is_nothing
    assert depends_on_both_sub_assets.op.ins["asset_2"].dagster_type.is_nothing

    res = materialize(
        [a_multi_asset, depends_on_one_sub_asset, depends_on_both_sub_assets],
        resources={"io_manager": TestingIOManager()},
    )
    assert res.success


def test_multi_asset_deps_via_mixed_types():
    @multi_asset(
        outs={
            "asset_1": AssetOut(),
            "asset_2": AssetOut(),
        }
    )
    def a_multi_asset():
        return None, None

    @asset(deps=[AssetKey("asset_1"), "asset_2"])
    def depends_on_both_sub_assets():
        return None

    assert len(depends_on_both_sub_assets.input_names) == 2
    assert depends_on_both_sub_assets.op.ins["asset_1"].dagster_type.is_nothing
    assert depends_on_both_sub_assets.op.ins["asset_2"].dagster_type.is_nothing

    res = materialize(
        [a_multi_asset, depends_on_both_sub_assets], resources={"io_manager": TestingIOManager()}
    )
    assert res.success


def test_multi_asset_deps_via_assets_definition_fails():
    @multi_asset(
        outs={
            "asset_1": AssetOut(),
            "asset_2": AssetOut(),
        }
    )
    def a_multi_asset():
        return None, None

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="For the multi_asset a_multi_asset, the available keys are: ",
    ):

        @asset(deps=[a_multi_asset])
        def depends_on_both_sub_assets():
            return None


def test_multi_asset_downstream_deps_via_assets_definition():
    @asset
    def asset_1():
        return None

    @multi_asset(deps=[asset_1], outs={"out1": AssetOut(), "out2": AssetOut()})
    def asset_2():
        return None, None

    assert len(asset_2.input_names) == 1
    assert asset_2.op.ins["asset_1"].dagster_type.is_nothing

    res = materialize([asset_1, asset_2], resources={"io_manager": TestingIOManager()})

    assert res.success


def test_multi_asset_downstream_deps_via_string():
    @asset
    def asset_1():
        return None

    @multi_asset(deps=["asset_1"], outs={"out1": AssetOut(), "out2": AssetOut()})
    def asset_2():
        return None, None

    assert len(asset_2.input_names) == 1
    assert asset_2.op.ins["asset_1"].dagster_type.is_nothing

    res = materialize([asset_1, asset_2], resources={"io_manager": TestingIOManager()})

    assert res.success


def test_multi_asset_downstream_deps_via_asset_key():
    @asset
    def asset_1():
        return None

    @multi_asset(deps=[AssetKey("asset_1")], outs={"out1": AssetOut(), "out2": AssetOut()})
    def asset_2():
        return None, None

    assert len(asset_2.input_names) == 1
    assert asset_2.op.ins["asset_1"].dagster_type.is_nothing

    res = materialize([asset_1, asset_2], resources={"io_manager": TestingIOManager()})
    assert res.success


def test_multi_asset_downstream_deps_via_mixed_types():
    @asset
    def via_definition():
        return None

    @asset
    def via_string():
        return None

    @asset
    def via_asset_key():
        return None

    @multi_asset(
        deps=[via_definition, "via_string", AssetKey("via_asset_key")],
        outs={"out1": AssetOut(), "out2": AssetOut()},
    )
    def downstream():
        return None, None

    assert len(downstream.input_names) == 3
    assert downstream.op.ins["via_definition"].dagster_type.is_nothing
    assert downstream.op.ins["via_string"].dagster_type.is_nothing
    assert downstream.op.ins["via_asset_key"].dagster_type.is_nothing

    res = materialize(
        [via_definition, via_string, via_asset_key, downstream],
        resources={"io_manager": TestingIOManager()},
    )
    assert res.success


def test_source_asset_deps_via_assets_definition():
    a_source_asset = SourceAsset("a_key")

    @asset(deps=[a_source_asset])
    def depends_on_source_asset():
        return None

    assert len(depends_on_source_asset.input_names) == 1
    assert depends_on_source_asset.op.ins["a_key"].dagster_type.is_nothing

    res = materialize([depends_on_source_asset], resources={"io_manager": TestingIOManager()})
    assert res.success


def test_source_asset_deps_via_string():
    a_source_asset = SourceAsset("a_key")  # noqa: F841

    @asset(deps=["a_key"])
    def depends_on_source_asset():
        return None

    assert len(depends_on_source_asset.input_names) == 1
    assert depends_on_source_asset.op.ins["a_key"].dagster_type.is_nothing

    res = materialize([depends_on_source_asset], resources={"io_manager": TestingIOManager()})
    assert res.success


def test_source_asset_deps_via_key():
    a_source_asset = SourceAsset("a_key")  # noqa: F841

    @asset(deps=[AssetKey("a_key")])
    def depends_on_source_asset():
        return None

    assert len(depends_on_source_asset.input_names) == 1
    assert depends_on_source_asset.op.ins["a_key"].dagster_type.is_nothing

    res = materialize([depends_on_source_asset], resources={"io_manager": TestingIOManager()})
    assert res.success


def test_interop():
    @asset
    def no_value_asset():
        return None

    @asset(io_manager_key="fs_io_manager")
    def value_asset() -> int:
        return 1

    @asset(
        deps=[no_value_asset],
    )
    def interop_asset(value_asset: int):
        assert value_asset == 1

    assert len(interop_asset.input_names) == 2
    assert interop_asset.op.ins["no_value_asset"].dagster_type.is_nothing
    assert interop_asset.op.ins["value_asset"].dagster_type.kind == DagsterTypeKind.SCALAR

    res = materialize(
        [no_value_asset, value_asset, interop_asset],
        resources={"io_manager": TestingIOManager(), "fs_io_manager": FilesystemIOManager()},
    )
    assert res.success


def test_non_existent_asset_key():
    @asset(deps=["not_real"])
    def my_asset():
        return None

    res = materialize([my_asset], resources={"io_manager": TestingIOManager()})

    assert res.success


def test_bad_types():
    class NotAnAsset:
        def __init__(self):
            self.foo = "bar"

    not_an_asset = NotAnAsset()

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(r"Cannot pass an instance of type .*" " to deps parameter of @asset"),
    ):

        @asset(deps=[not_an_asset])
        def my_asset():
            return None


def test_dep_via_deps_and_fn():
    @asset
    def the_upstream_asset():
        return 1

    with pytest.raises(
        DagsterInvalidDefinitionError,
        # this is a known bad error experience. TODO - update the error to be helpful
        match=(
            "@op 'depends_on_upstream_asset' decorated function has parameter 'the_upstream_asset'"
            " that is one of the input_defs of type 'Nothing' which should not be included since no"
            " data will be passed for it."
        ),
    ):

        @asset(deps=[the_upstream_asset])
        def depends_on_upstream_asset(the_upstream_asset):
            return None

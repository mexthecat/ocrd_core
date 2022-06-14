import os
import pathlib
import pdb

from ocrd.resource_manager import OcrdResourceManager
from ocrd_utils.os import get_ocrd_tool_json

from pytest import raises, fixture
from tests.base import main

CONST_RESOURCE_YML = 'resources.yml'
CONST_RESOURCE_URL_LAYOUT = 'https://github.com/tesseract-ocr/tessdata_best/raw/main/bos.traineddata'

@fixture(autouse=True)
def drop_get_ocrd_tool_json_cache():
    get_ocrd_tool_json.cache_clear()
    yield

def test_resources_manager_config_default(monkeypatch, tmp_path):

    # arrange
    monkeypatch.setenv('HOME', str(tmp_path))

    # act
    mgr = OcrdResourceManager()

    # assert
    default_config_dir = os.path.join(os.environ['HOME'], '.config', 'ocrd')
    f = pathlib.Path(default_config_dir) / CONST_RESOURCE_YML
    assert f.exists()
    assert f == mgr.user_list
    assert mgr.add_to_user_database('ocrd-foo', f)
    # pdb.set_trace()

    mgr.list_installed()
    proc = 'ocrd-tesserocr-recognize'
    # TODO mock request
    fpath = mgr.download(proc, CONST_RESOURCE_URL_LAYOUT, mgr.location_to_resource_dir('data'))
    assert fpath.exists()
    assert mgr.add_to_user_database(proc, fpath)


def test_resources_manager_from_environment(tmp_path, monkeypatch):

    # arrange
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path))
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path))
    monkeypatch.setenv('HOME', str(tmp_path))

    # act
    mgr = OcrdResourceManager()

    # assert
    f = tmp_path / 'ocrd' / CONST_RESOURCE_YML
    assert f.exists()
    assert f == mgr.user_list
    assert mgr.add_to_user_database('ocrd-foo', f)
    mgr.list_installed()
    proc = 'ocrd-tesserocr-recognize'
    fpath = mgr.download(proc, CONST_RESOURCE_URL_LAYOUT, mgr.location_to_resource_dir('data'))
    assert fpath.exists()
    assert mgr.add_to_user_database(proc, fpath)
    assert mgr.userdir == str(tmp_path)


def test_resources_manager_config_explicite(tmp_path):

    # act
    mgr = OcrdResourceManager(xdg_config_home=str(tmp_path))

    # assert
    f = tmp_path / 'ocrd' / CONST_RESOURCE_YML
    assert f.exists()
    assert f == mgr.user_list
    assert mgr.add_to_user_database('ocrd-foo', f)
    mgr.list_installed()
    proc = 'ocrd-tesserocr-recognize'
    fpath = mgr.download(proc, CONST_RESOURCE_URL_LAYOUT, mgr.location_to_resource_dir('data'))
    assert fpath.exists()
    assert mgr.add_to_user_database(proc, fpath)

def test_resources_manager_config_explicit_invalid(tmp_path):

    # act
    (tmp_path / 'ocrd').mkdir()
    (tmp_path / 'ocrd' / CONST_RESOURCE_YML).write_text('::INVALID::')

    # assert
    with raises(ValueError, match='is invalid'):
        OcrdResourceManager(xdg_config_home=tmp_path)

def test_find_resources(tmp_path):

    # act
    f = tmp_path / 'ocrd-foo' / 'foo.bar'
    f.parent.mkdir()
    f.write_text('foobar')
    mgr = OcrdResourceManager(xdg_config_home=tmp_path)

    # assert
    assert mgr.find_resources(executable='ocrd-foo') == []
    assert mgr.add_to_user_database('ocrd-foo', f, url='http://foo/bar')
    assert 'ocrd-foo' in [x for x, _ in mgr.find_resources()]
    assert 'ocrd-foo' in [x for x, _ in mgr.find_resources(url='http://foo/bar')]

def test_parameter_usage(tmp_path):
    mgr = OcrdResourceManager(xdg_config_home=tmp_path)
    assert mgr.parameter_usage('foo.bar') == 'foo.bar'
    assert mgr.parameter_usage('foo.bar', 'without-extension') == 'foo'
    with raises(ValueError, match='No such usage'):
        mgr.parameter_usage('foo.bar', 'baz')

def test_default_resource_dir(tmp_path):
    mgr = OcrdResourceManager(xdg_data_home=tmp_path)
    assert mgr.xdg_config_home != mgr.xdg_data_home
    assert mgr.default_resource_dir == str(mgr.xdg_data_home / 'ocrd-resources')

def test_list_available(tmp_path):
    mgr = OcrdResourceManager(xdg_data_home=tmp_path)
    res = mgr.list_available()
    assert len(res) > 0

def test_list_available_with_unknown_executable(tmp_path):
    mgr = OcrdResourceManager(xdg_data_home=tmp_path)
    res = mgr.list_available(executable="ocrd-non-existing-processor")
    assert len(res[0][1]) == 0

def test_date_as_string(tmp_path):
    mgr = OcrdResourceManager(xdg_data_home=tmp_path)
    test_list = tmp_path / 'test-list.yml'
    with open(test_list, 'w', encoding='utf-8') as fout:
        fout.write("""\
    ocrd-eynollah-segment:
      - url: https://qurator-data.de/eynollah/2022-04-05/models_eynollah_renamed.tar.gz
        name: 2022-04-05
        description: models for eynollah
        type: tarball
        path_in_archive: 'models_eynollah'
        size: 1889719626
        """)
    mgr.load_resource_list(test_list)
    mgr.list_available(executable='ocrd-eynollah-segment')

if __name__ == "__main__":
    main(__file__)

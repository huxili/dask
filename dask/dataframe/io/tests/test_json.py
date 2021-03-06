import os
import pandas as pd
import pytest

import dask.dataframe as dd
from dask.utils import tmpfile, tmpdir
from dask.dataframe.utils import assert_eq


df = pd.DataFrame({'x': ['a', 'b', 'c', 'd'],
                   'y': [1, 2, 3, 4]})


@pytest.mark.parametrize('orient', ['split', 'records', 'index', 'columns',
                                    'values'])
def test_read_json_basic(orient):
    with tmpfile('json') as f:
        df.to_json(f, orient=orient, lines=False)
        actual = dd.read_json(f, orient=orient, lines=False)
        actual_pd = pd.read_json(f, orient=orient, lines=False)

        out = actual.compute()
        assert_eq(out, actual_pd)
        if orient == 'values':
            out.columns = list(df.columns)
        assert_eq(out, df)


@pytest.mark.parametrize('orient', ['split', 'records', 'index', 'columns',
                                    'values'])
def test_write_json_basic(orient):
    with tmpdir() as path:
        fn = os.path.join(path, '1.json')
        df.to_json(fn, orient=orient, lines=False)
        actual = dd.read_json(fn, orient=orient, lines=False)
        out = actual.compute()
        if orient == 'values':
            out.columns = list(df.columns)
        assert_eq(out, df)


def test_read_json_error():
    with tmpfile('json') as f:
        with pytest.raises(ValueError):
            df.to_json(f, orient='split', lines=True)
        df.to_json(f, orient='split', lines=False)
        with pytest.raises(ValueError):
            dd.read_json(f, orient='split', blocksize=1)


@pytest.mark.parametrize('block', [5, 15, 33, 200, 90000])
def test_read_chunked(block):
    with tmpdir() as path:
        fn = os.path.join(path, '1.json')
        df.to_json(fn, orient='records', lines=True)
        d = dd.read_json(fn, blocksize=block, sample=10)
        assert (d.npartitions > 1) or (block > 50)
        assert_eq(d, df, check_index=False)

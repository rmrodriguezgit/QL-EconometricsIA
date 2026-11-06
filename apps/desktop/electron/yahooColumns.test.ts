import test from 'node:test';
import assert from 'node:assert/strict';
import {tickerAlias,yahooColumns,knownSourceColumns} from '../src/sourceColumns.ts';

test('alias de tickers de Yahoo Finance iguales a los del motor',()=>{
 assert.equal(tickerAlias('aapl'),'aapl');
 assert.equal(tickerAlias('WALMEX.MX'),'walmex');
 assert.equal(tickerAlias('^MXX'),'ipc_mexico');
 assert.equal(tickerAlias('MXN=X'),'usd_mxn');
 assert.equal(tickerAlias('ZZZ.MX'),'zzz_mx');
 assert.equal(tickerAlias('7203.T'),'t_7203_t');
});

test('columnas del nodo yfinance: periodo, activos y el índice elegido',()=>{
 assert.deepEqual(yahooColumns('AAPL\nMSFT: micro','^GSPC'),['periodo','aapl','micro','sp500']);
 assert.deepEqual(yahooColumns('WALMEX.MX','ninguno'),['periodo','walmex']);
 assert.deepEqual(knownSourceColumns({id:'y',type:'yfinance',node_version:'1.0.0',parameters:{tickers:'BTC-USD',index:'^IXIC'},position:{x:0,y:0}} as never),['periodo','bitcoin','nasdaq']);
});

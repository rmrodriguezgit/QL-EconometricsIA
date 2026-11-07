import test from 'node:test';
import assert from 'node:assert/strict';
import {formatNumber,numberFormat,scientific} from '../src/numberFormat.ts';
import {axisScale} from '../src/axisFormat.ts';

test('miles de millones o más en notación científica',()=>{
 assert.equal(formatNumber(25_462_700_000_000),'2.546 × 10¹³');
 assert.equal(formatNumber(-1_250_000_000),'-1.25 × 10⁹');
 assert.equal(formatNumber(999_999_999),'999,999,999');
 assert.equal(formatNumber(9_999_900_000),'1 × 10¹⁰');
 assert.equal(numberFormat({maximumFractionDigits:2}).format(1234.567),'1,234.57');
 assert.equal(scientific(0.0000123),'1.23 × 10⁻⁵');
});

test('eje en modo normal conserva números completos',()=>{
 const scale=axisScale([2e12,3e12],'normal',value=>formatNumber(value));
 assert.equal(scale.tick(2e12),'2,000,000,000,000');
});

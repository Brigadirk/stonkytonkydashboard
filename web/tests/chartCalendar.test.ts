import {describe,expect,it} from 'vitest';
import {chartCalendar} from '../src/chartCalendar';

describe('chart dates with recorded closing prices',()=>{
  it('collapses weekends, holidays and missing weekday prices while preserving future dates',()=>{
    const dates=['2026-09-03','2026-09-04','2026-09-08','2026-09-10'];
    const calendar=chartCalendar(dates.map(date=>({date,price:100})));
    expect(calendar.missing).toEqual(['2026-09-05','2026-09-06','2026-09-07','2026-09-09']);
    expect(dates.map(calendar.position)).toEqual([0,1,2,3]);
    expect(calendar.position('2026-09-12')-calendar.position('2026-09-10')).toBe(2);
    expect(calendar.position('2027-09-10')-calendar.position('2026-09-10')).toBe(365);
    expect(calendar.cursorDate('2026-09-07')).toBe('2026-09-08');
    expect(calendar.cursorDate('2026-09-09')).toBe('2026-09-10');
    expect(calendar.cursorDate('2026-09-04')).toBe('2026-09-04');
    expect(calendar.cursorDate('2026-09-12')).toBe('2026-09-12');
    expect(calendar.cursorDate('2026-09-02')).toBeNull();
  });
  it('uses each listing’s actual records, including an unusual weekend close',()=>{
    const calendar=chartCalendar([{date:'2026-09-07',price:101},{date:'2026-09-04',price:100},{date:'2026-09-05',price:0},{date:'2026-09-06',price:NaN}]);
    expect(calendar.missing).toEqual(['2026-09-06']);
    expect(calendar.position('2026-09-05')).toBe(1);
    expect(calendar.position('2026-09-07')).toBe(2);
    expect(chartCalendar([]).missing).toEqual([]);
    expect(chartCalendar([{date:'2026-09-04',price:100}]).missing).toEqual([]);
  });
});

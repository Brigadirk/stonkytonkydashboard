import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';

test('entry windows change current bands while projected bands and dated targets stay fixed in single, overlay and combined views',async({page})=>{
  const data=JSON.parse(await readFile(new URL('../public/data/dashboard.json',import.meta.url),'utf8'));
  const company=data.companies.find((c:{id:string})=>c.id==='nvidia');
  const members=company.series.filter((s:{accounting_basis:string})=>s.accounting_basis==='reported_diluted');
  const anchor=members.find((s:{firm:string})=>s.firm==='Morningstar');
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  for(const mode of ['single','overlay','ensemble']){
    await page.goto(`/?company=nvidia&series=${anchor.id}&mode=${mode}&estimatorIds=${members.map((s:{id:string})=>s.id).join(',')}&window=90&targetSigma=0`);
    await expect(page.getByTestId('simple-target')).not.toContainText('—');
    const target=await page.getByTestId('simple-target').innerText();
    await page.getByRole('button',{name:'Advanced',exact:true}).click();
    const panel=page.getByTestId('projection-panel');
    await expect(panel.locator('.metric strong').nth(1)).toHaveText(target);
    const future=()=>page.getByTestId('chart-price').evaluate(el=>{
      const data=(el as unknown as {data?:{name:string;x:string[];y:(number|null)[]}[]}).data||[];
      return data.filter(t=>t.name==='All 12-month targets'||t.name.endsWith('12-month selected target')||t.name.includes(' · Projected ')).map(t=>({name:t.name,x:t.x,y:t.y}));
    });
    await expect.poll(async()=> (await future()).length).toBe(mode==='overlay'?18:9);
    const baseline=await future(),historical:number[][]=[];
    for(const window of [90,180,365]){
      await page.getByLabel('Window in days',{exact:true}).fill(String(window));
      await expect(panel.locator('.metric strong').nth(1)).toHaveText(target);
      await expect.poll(future).toEqual(baseline);
      historical.push(await page.getByTestId('chart-price').evaluate(el=>{
        const data=(el as unknown as {data?:{name:string;y:number[]}[]}).data||[];
        return data.filter(t=>t.name==='Rolling median'||t.name.endsWith('Median price')).map(t=>t.y.at(-1)!);
      }));
    }
    expect(historical[0]).not.toEqual(historical[2]);
    await page.getByRole('button',{name:'Simple view',exact:true}).click();
    await expect(page.getByTestId('simple-target')).toHaveText(target);
  }
  expect(errors).toEqual([]);
});

import { defineConfig } from '@playwright/test';
const port=process.env.FORWARD_TEST_PORT||'5178';
if(!/^\d+$/.test(port)||Number(port)<1024||Number(port)>65535)throw new Error('Invalid FORWARD_TEST_PORT');
export default defineConfig({testDir:'./tests',testMatch:'**/*.browser.ts',timeout:45000,use:{baseURL:`http://127.0.0.1:${port}`,headless:true},webServer:{command:`npm run preview -- --port ${port}`,url:`http://127.0.0.1:${port}`,reuseExistingServer:!process.env.CI,timeout:30000}});

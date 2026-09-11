import { defineConfig } from '@playwright/test';
export default defineConfig({testDir:'./tests',testMatch:'**/*.browser.ts',timeout:45000,use:{baseURL:'http://127.0.0.1:5178',headless:true},webServer:{command:'npm run preview',url:'http://127.0.0.1:5178',reuseExistingServer:true,timeout:30000}});

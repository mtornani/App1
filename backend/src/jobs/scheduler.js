const cron = require('cron');
const { runFullRefresh } = require('../services/agent');

// Scheduler per aggiornamenti automatici
const scheduledJobs = [];

// Job giornaliero alle 2:00 AM
const dailyJob = new cron.CronJob('0 0 2 * * *', async () => {
  console.log('📅 Running daily refresh job...');
  try {
    await runFullRefresh();
    console.log('✅ Daily refresh completed');
  } catch (error) {
    console.error('❌ Daily refresh failed:', error);
  }
});

// Job settimanale alla domenica alle 3:00 AM
const weeklyJob = new cron.CronJob('0 0 3 * * 0', async () => {
  console.log('📅 Running weekly deep refresh job...');
  try {
    await runFullRefresh();
    console.log('✅ Weekly deep refresh completed');
  } catch (error) {
    console.error('❌ Weekly deep refresh failed:', error);
  }
});

function startScheduler() {
  dailyJob.start();
  weeklyJob.start();
  scheduledJobs.push(dailyJob, weeklyJob);
  console.log('⏰ Scheduler started');
}

function stopScheduler() {
  scheduledJobs.forEach(job => job.stop());
  console.log('⏰ Scheduler stopped');
}

module.exports = {
  startScheduler,
  stopScheduler
};

const express = require('express');
const {
  getNotifications,
  markAsRead,
  markAllAsRead,
  clearAll,
  getAnalytics,
} = require('../controllers/notificationController');
const { protect } = require('../middleware/authMiddleware');

const router = express.Router();

router.get('/', protect, getNotifications);
router.get('/analytics', protect, getAnalytics);
router.put('/read-all', protect, markAllAsRead);
router.put('/:id/read', protect, markAsRead);
router.delete('/clear', protect, clearAll);

module.exports = router;

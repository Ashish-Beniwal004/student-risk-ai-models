const Notification = require('../models/Notification');

// @desc  Get all notifications (for header bell)
// @route GET /api/notifications
const getNotifications = async (req, res) => {
  try {
    const query = {};

    // Students only see their own notifications
    if (req.user.role === 'STUDENT') {
      query.studentId = req.user._id;
    }

    const notifications = await Notification.find(query)
      .sort({ createdAt: -1 })
      .limit(20);

    const unreadCount = await Notification.countDocuments({ ...query, isRead: false });

    res.json({ notifications, unreadCount });
  } catch (error) {
    console.error('Get notifications error:', error);
    res.status(500).json({ message: 'Failed to fetch notifications' });
  }
};

// @desc  Mark a notification as read
// @route PUT /api/notifications/:id/read
const markAsRead = async (req, res) => {
  try {
    const notification = await Notification.findByIdAndUpdate(
      req.params.id,
      { isRead: true },
      { new: true }
    );

    if (!notification) {
      return res.status(404).json({ message: 'Notification not found' });
    }

    res.json(notification);
  } catch (error) {
    console.error('Mark read error:', error);
    res.status(500).json({ message: 'Failed to update notification' });
  }
};

// @desc  Mark all notifications as read
// @route PUT /api/notifications/read-all
const markAllAsRead = async (req, res) => {
  try {
    const query = {};
    if (req.user.role === 'STUDENT') {
      query.studentId = req.user._id;
    }

    await Notification.updateMany({ ...query, isRead: false }, { isRead: true });
    res.json({ message: 'All notifications marked as read' });
  } catch (error) {
    console.error('Mark all read error:', error);
    res.status(500).json({ message: 'Failed to update notifications' });
  }
};

// @desc  Delete all notifications
// @route DELETE /api/notifications/clear
const clearAll = async (req, res) => {
  try {
    await Notification.deleteMany({});
    res.json({ message: 'All notifications cleared' });
  } catch (error) {
    console.error('Clear notifications error:', error);
    res.status(500).json({ message: 'Failed to clear notifications' });
  }
};

// @desc  Get risk analytics for teacher/authority dashboards
// @route GET /api/notifications/analytics
const getAnalytics = async (req, res) => {
  try {
    const allNotifs = await Notification.find().sort({ createdAt: -1 }).limit(100);

    const total = allNotifs.length;
    const highRisk = allNotifs.filter(n => n.riskLevel === 'HIGH').length;
    const medRisk = allNotifs.filter(n => n.riskLevel === 'MEDIUM').length;
    const lowRisk = allNotifs.filter(n => n.riskLevel === 'LOW').length;
    const avgScore = total > 0
      ? (allNotifs.reduce((sum, n) => sum + n.riskScore, 0) / total).toFixed(1)
      : 0;

    res.json({
      total,
      highRisk,
      medRisk,
      lowRisk,
      avgScore: parseFloat(avgScore),
      recent: allNotifs.slice(0, 10),
    });
  } catch (error) {
    console.error('Analytics error:', error);
    res.status(500).json({ message: 'Failed to fetch analytics' });
  }
};

module.exports = { getNotifications, markAsRead, markAllAsRead, clearAll, getAnalytics };

const mongoose = require('mongoose');

const notificationSchema = new mongoose.Schema({
  studentId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
  },
  studentName: {
    type: String,
    required: true,
  },
  riskScore: {
    type: Number,
    required: true,
  },
  riskLevel: {
    type: String,
    enum: ['HIGH', 'MEDIUM', 'LOW'],
    required: true,
  },
  message: {
    type: String,
    required: true,
  },
  isRead: {
    type: Boolean,
    default: false,
  },
  breakdown: {
    dropoutScore: Number,
    wellbeingScore: Number,
    depressionScore: Number,
  },
}, {
  timestamps: true,
});

module.exports = mongoose.model('Notification', notificationSchema);

const axios = require('axios');
const Notification = require('../models/Notification');
const User = require('../models/User');

const FLASK_URL = process.env.ML_SERVICE_URL || process.env.FLASK_SERVICE_URL || 'http://localhost:8000';
const HIGH_RISK_THRESHOLD = 70;

// @desc  Run ML prediction for a student
// @route POST /api/predict
const runPrediction = async (req, res) => {
  try {
    const { attendance, gpa, assignmentCompletion, midtermScore, targetEmail, targetDepartment } = req.body;

    // Validate presence of required fields
    if (attendance === undefined || gpa === undefined ||
        assignmentCompletion === undefined || midtermScore === undefined) {
      return res.status(400).json({
        message: 'attendance, gpa, assignmentCompletion, and midtermScore are required',
      });
    }

    let notifStudentId = req.user?.role === 'STUDENT' ? req.user._id : null;
    let notifName = req.user?.name || 'Unknown Student';
    let isAssigned = false;

    if (targetEmail && targetDepartment) {
      if (req.user.role !== 'TEACHER' && req.user.role !== 'AUTHORITY') {
        return res.status(403).json({ message: 'Unauthorized to assign predictions to other students.' });
      }

      const matchingStudent = await User.findOne({ 
        email: targetEmail.toLowerCase(), 
        department: { $regex: new RegExp(`^${targetDepartment}$`, 'i') },
        role: 'STUDENT'
      });

      if (!matchingStudent) {
        return res.status(404).json({ message: 'Student email and department do not match any records.' });
      }

      notifStudentId = matchingStudent._id;
      notifName = matchingStudent.name;
      isAssigned = true;
    }

    // Call Flask ML service
    let flaskResponse;
    try {
      flaskResponse = await axios.post(`${FLASK_URL}/predict`, {
        attendance: Number(attendance),
        gpa: Number(gpa),
        assignmentCompletion: Number(assignmentCompletion),
        midtermScore: Number(midtermScore),
      }, {
        timeout: 30000, // 30s timeout for model inference
      });
    } catch (flaskError) {
      const msg = flaskError.response?.data?.error || flaskError.message;
      console.error('Flask service error:', msg);
      return res.status(503).json({
        message: `ML service unavailable: ${msg}`,
      });
    }

    const prediction = flaskResponse.data;
    const { riskScore, riskLevel, topFactors, breakdown } = prediction;

    // Auto-create notification if high risk (riskScore >= 70) or if explicitly assigned
    if (riskScore >= HIGH_RISK_THRESHOLD || isAssigned) {
      try {
        if (notifStudentId) {
          const alertPrefix = riskScore >= HIGH_RISK_THRESHOLD ? '⚠️ HIGH RISK ALERT:' : 'ℹ️ PREDICTION UPDATE:';
          await Notification.create({
            studentId: notifStudentId,
            studentName: notifName,
            riskScore,
            riskLevel,
            message: `${alertPrefix} ${notifName} has a risk score of ${riskScore.toFixed(1)}/100. ${
              topFactors[0] || 'See dashboard for details.'
            }`,
            breakdown,
          });
          console.log(`[ALERT] Notification created for student: ${notifName} (score: ${riskScore})`);
        }
      } catch (notifError) {
        // Non-fatal — log but don't fail the prediction response
        console.error('Failed to create notification:', notifError.message);
      }
    }

    return res.json(prediction);
  } catch (error) {
    console.error('Prediction controller error:', error);
    res.status(500).json({ message: 'Internal server error during prediction' });
  }
};

// @desc  Get all predictions history (for authority dashboard)
// @route GET /api/predict/history
const getPredictionHistory = async (req, res) => {
  try {
    const notifications = await Notification.find()
      .sort({ createdAt: -1 })
      .limit(50)
      .populate('studentId', 'name email department');

    res.json(notifications);
  } catch (error) {
    console.error('History fetch error:', error);
    res.status(500).json({ message: 'Failed to fetch prediction history' });
  }
};

module.exports = { runPrediction, getPredictionHistory };

const axios = require('axios');
const Notification = require('../models/Notification');
const User = require('../models/User');

const FLASK_URL = process.env.ML_SERVICE_URL || process.env.FLASK_SERVICE_URL || 'http://localhost:8000';
const HIGH_RISK_THRESHOLD = 70;

// ─────────────────────────────────────────────────────────────────────────────
// JS FALLBACK — mirrors the Python risk_fusion logic.
// Used when the Flask / Render service is unavailable (502, cold start, timeout).
// Weights: dropout 40 %, wellbeing 30 %, depression 30 %
// ─────────────────────────────────────────────────────────────────────────────
function computeFallbackPrediction(attendance, gpa, assignmentCompletion, midtermScore) {
  const a = Math.max(0, Math.min(100, attendance)) / 100;       // 0–1
  const g = Math.max(0, Math.min(10,  gpa))        / 10;        // 0–1
  const s = Math.max(0, Math.min(100, assignmentCompletion)) / 100;
  const m = Math.max(0, Math.min(100, midtermScore))          / 100;

  // Each "model" score 0–100  (higher = more risk)
  const dropoutScore   = Math.round((1 - (a * 0.35 + g * 0.40 + s * 0.25)) * 100 * 10) / 10;
  const wellbeingScore = Math.round((1 - (a * 0.30 + g * 0.20 + s * 0.25 + m * 0.25)) * 100 * 10) / 10;
  const deprScore      = Math.round((1 - (g * 0.35 + m * 0.35 + a * 0.30)) * 100 * 10) / 10;

  const finalScore = Math.round(
    (dropoutScore * 0.40 + wellbeingScore * 0.30 + deprScore * 0.30) * 100
  ) / 100;

  const riskLevel = finalScore >= 60 ? 'HIGH' : finalScore >= 30 ? 'MEDIUM' : 'LOW';

  // Build plain-English factors
  const factors = [];
  if (attendance < 60)           factors.push(`Low attendance (${attendance.toFixed(0)}%) — critical engagement risk`);
  if (gpa < 5.0)                 factors.push(`Very low CGPA (${gpa.toFixed(1)}/10) — academic failure risk`);
  if (assignmentCompletion < 50) factors.push(`Poor assignment completion (${assignmentCompletion.toFixed(0)}%)`);
  if (midtermScore < 40)         factors.push(`Critical midterm score (${midtermScore.toFixed(0)}%) — urgent intervention needed`);
  if (dropoutScore > 60)         factors.push(`High academic dropout risk (${dropoutScore.toFixed(1)}/100)`);
  if (wellbeingScore > 60)       factors.push(`High wellbeing concern (${wellbeingScore.toFixed(1)}/100)`);
  if (deprScore > 60)            factors.push(`Elevated mental health indicators (${deprScore.toFixed(1)}/100)`);
  if (factors.length === 0)      factors.push('All academic indicators within normal range');

  return {
    riskScore:  finalScore,
    riskLevel,
    topFactors: factors.slice(0, 5),
    breakdown:  { dropoutScore, wellbeingScore, depressionScore: deprScore },
    source:     'fallback', // internal flag only
  };
}

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

    // ── Try Flask service first; fall back to JS computation on any error ────
    let prediction;

    try {
      const flaskResponse = await axios.post(`${FLASK_URL}/predict`, {
        attendance:           Number(attendance),
        gpa:                  Number(gpa),
        assignmentCompletion: Number(assignmentCompletion),
        midtermScore:         Number(midtermScore),
      }, {
        timeout: 15000, // 15 s — don't wait forever on a cold Render start
      });
      prediction = flaskResponse.data;
      console.log('[Predict] Flask service responded OK');
    } catch (flaskError) {
      const msg = flaskError.response?.data?.error || flaskError.message;
      console.warn(`[Predict] Flask unavailable (${msg}). Using JS fallback.`);
      prediction = computeFallbackPrediction(
        Number(attendance),
        Number(gpa),
        Number(assignmentCompletion),
        Number(midtermScore),
      );
    }

    const { riskScore, riskLevel, topFactors, breakdown } = prediction;

    // Auto-create notification if high risk (riskScore >= 70) or if explicitly assigned
    if (riskScore >= HIGH_RISK_THRESHOLD || isAssigned) {
      try {
        if (notifStudentId) {
          const alertPrefix = riskScore >= HIGH_RISK_THRESHOLD ? '⚠️ HIGH RISK ALERT:' : 'ℹ️ PREDICTION UPDATE:';
          await Notification.create({
            studentId:   notifStudentId,
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
        console.error('Failed to create notification:', notifError.message);
      }
    }

    // Strip the internal `source` flag before sending to client
    const { source, ...clientPayload } = prediction;
    return res.json(clientPayload);

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

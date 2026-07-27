const express = require('express');
const { runPrediction, getPredictionHistory } = require('../controllers/predictController');
const { protect } = require('../middleware/authMiddleware');

const router = express.Router();

// Protected: any authenticated user can run a prediction
router.post('/', protect, runPrediction);
router.get('/history', protect, getPredictionHistory);

module.exports = router;

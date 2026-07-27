require('dotenv').config();
const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
const User = require('./models/User');

const MONGO_URI = process.env.MONGODB_URI || process.env.MONGO_URI || 'mongodb://localhost:27017/disha';

const seedUsers = [
  // Students
  {
    name: 'Aarav Sharma',
    email: 'aarav.student@disha.edu',
    password: 'password123',
    role: 'STUDENT',
    department: 'Computer Science',
  },
  {
    name: 'Priya Verma',
    email: 'priya.student@disha.edu',
    password: 'password123',
    role: 'STUDENT',
    department: 'Electronics Engineering',
  },
  // Teachers
  {
    name: 'Dr. Rajan Mehta',
    email: 'rajan.teacher@disha.edu',
    password: 'password123',
    role: 'TEACHER',
    department: 'Computer Science',
  },
  {
    name: 'Prof. Sunita Reddy',
    email: 'sunita.teacher@disha.edu',
    password: 'password123',
    role: 'TEACHER',
    department: 'Electronics Engineering',
  },
  // Authorities
  {
    name: 'Dr. Nalini Iyer',
    email: 'nalini.authority@disha.edu',
    password: 'password123',
    role: 'AUTHORITY',
    department: 'Academic Affairs',
  },
  {
    name: 'Mr. Vikram Nair',
    email: 'vikram.authority@disha.edu',
    password: 'password123',
    role: 'AUTHORITY',
    department: 'Student Welfare',
  },
];

async function seed() {
  try {
    await mongoose.connect(MONGO_URI);
    console.log('✅ MongoDB connected');

    // Clear existing users
    await User.deleteMany({});
    console.log('🗑️  Cleared existing users');

    // Insert with plain passwords (pre-save hook hashes them)
    for (const userData of seedUsers) {
      await User.create(userData);
      console.log(`✅ Seeded: ${userData.name} (${userData.role}) — ${userData.email}`);
    }

    console.log('\n🎉 Seeding complete! Login credentials:');
    console.log('━'.repeat(55));
    seedUsers.forEach(u => {
      console.log(`  ${u.role.padEnd(10)} | ${u.email.padEnd(35)} | password123`);
    });
    console.log('━'.repeat(55));

  } catch (error) {
    console.error('❌ Seeding failed:', error.message);
  } finally {
    await mongoose.disconnect();
    console.log('Database disconnected.');
    process.exit(0);
  }
}

seed();

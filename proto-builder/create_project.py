#!/usr/bin/env python3
"""
create_project.py

Utility for:
1. Parsing an XML document describing a project.
2. Creating directories and files specified by that XML.
3. Executing a project creation command if specified.
4. Printing setup and run instructions.

Expected XML Structure:

<developer_output>
  <project_structure>
    <dir>greentrack</dir>
    <dir>greentrack/backend</dir>
    ...
  </project_structure>
  <setup><![CDATA[ ... ]]></setup>
  <files>
    <file>
      <path>backend/package.json</path>
      <content><![CDATA[
        ...some code...
      ]]></content>
    </file>
    ...
  </files>
  <run_deploy_steps><![CDATA[ ... ]]></run_deploy_steps>
  <misc_content><![CDATA[ ... ]]></misc_content>
  <project_creation_command><![CDATA[ ... ]]></project_creation_command>
</developer_output>

Usage:
  python create_project.py path/to/your.xml
"""

import os
import re
import sys
import subprocess
import traceback
from xml.etree import ElementTree as ET


def parse_developer_xml(xml_str: str):
    """
    Parses the given XML string and returns a dictionary with the keys:
      'project_structure': list of directory paths
      'setup': text from <setup>
      'files': dict {file_path: file_content}
      'run_deploy_steps': text from <run_deploy_steps>
      'misc_content': text from <misc_content>
      'project_creation_command': text from <project_creation_command>
    Raises ValueError if parsing fails.
    """
    try:
        root = ET.fromstring(xml_str.strip())
        if root.tag != "developer_output":
            raise ValueError("Root element must be <developer_output>")

        data = {
            "project_structure": [],
            "setup": "",
            "files": {},
            "run_deploy_steps": "",
            "misc_content": "",
            "project_creation_command": "",
        }

        # 1. project_structure
        ps_node = root.find("project_structure")
        if ps_node is not None:
            for d in ps_node.findall("dir"):
                if d.text:
                    data["project_structure"].append(d.text.strip())

        # 2. setup
        setup_node = root.find("setup")
        if setup_node is not None and setup_node.text:
            data["setup"] = setup_node.text.strip()

        # 3. files
        files_node = root.find("files")
        if files_node is not None:
            for fnode in files_node.findall("file"):
                p = fnode.find("path")
                c = fnode.find("content")
                if p is not None and c is not None:
                    path_val = p.text.strip()
                    # We'll keep the <code> tags for now and remove them when writing the file
                    content_val = c.text
                    data["files"][path_val] = content_val if content_val else ""

        # 4. run_deploy_steps
        rds_node = root.find("run_deploy_steps")
        if rds_node is not None and rds_node.text:
            data["run_deploy_steps"] = rds_node.text.strip()

        # 5. misc_content
        mc_node = root.find("misc_content")
        if mc_node is not None and mc_node.text:
            data["misc_content"] = mc_node.text.strip()

        # 6. project_creation_command
        pcc_node = root.find("project_creation_command")
        if pcc_node is not None and pcc_node.text:
            data["project_creation_command"] = pcc_node.text.strip()

        return data

    except Exception as e:
        raise ValueError(f"Error parsing developer_output XML: {e}")


def create_project_from_data(data: dict):
    """
    Given a dictionary with the fields:
      project_structure (list of dirs),
      setup (str),
      files (dict of { path: content }),
      run_deploy_steps (str),
      misc_content (str),
      project_creation_command (str),
    this function creates the project structure, writes files, and prints setup info.
    If a project_creation_command is available, we run it, then still create directories/files.
    """

    # 1) Run the project creation command if provided.
    project_creation_cmd = data.get("project_creation_command", "").strip()
    if project_creation_cmd:
        print("Executing project creation command:")
        print(project_creation_cmd)
        # try:
        #     subprocess.run(project_creation_cmd, shell=True, check=True)
        # except Exception as cmd_err:
        #     print(f"Failed to execute project creation command: {cmd_err}")

    # 2) Create directories from project_structure
    for directory in data.get("project_structure", []):
        directory = directory.strip()
        if directory:
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"Created directory: {directory}")
            except Exception as e:
                print(f"Failed to create directory '{directory}': {e}")

    # 3) Create files
    files_dict = data.get("files", {})
    for fpath, content in files_dict.items():
        print(f"Creating file: {fpath}")
        # remove <code>...</code> if present
        cleaned = re.sub(r"</?code>", "", content or "").strip()
        dirpath = os.path.dirname(fpath)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        try:
            with open(fpath, "w") as fp:
                fp.write(cleaned)
            print(f"Created file: {fpath}")
        except Exception as file_err:
            print(f"Error creating file '{fpath}': {file_err}")

    # 4) Print setup/run instructions & misc
    print("\n--- Setup Instructions ---")
    print(data.get("setup", ""))
    print("\n--- Run Instructions ---")
    print(data.get("run_deploy_steps", ""))
    if data.get("misc_content", "").strip():
        print("\n--- Miscellaneous Information ---")
        print(data["misc_content"])


def main(xml_path: str):
    """
    Main entry point: read the XML from the given file, parse it, and create the project structure.
    """
    if not os.path.isfile(xml_path):
        print(f"Error: '{xml_path}' is not a valid file.")
        sys.exit(1)

    try:
        with open(xml_path, "r", encoding="utf-8") as f:
            xml_str = f.read()
        data = parse_developer_xml(xml_str)
        create_project_from_data(data)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    xml_str = """
<developer_output>
  <project_structure>
    <dir>greentrack</dir>
    <dir>greentrack/backend</dir>
    <dir>greentrack/frontend</dir>
    <dir>greentrack/backend/models</dir>
    <dir>greentrack/backend/routes</dir>
    <dir>greentrack/frontend/src</dir>
    <dir>greentrack/frontend/src/components</dir>
    <dir>greentrack/frontend/src/services</dir>
  </project_structure>
  <setup>
    <![CDATA[
    # GreenTrack Setup Instructions

    ## Prerequisites
    - **Node.js** (v14 or later)
    - **npm** (comes with Node.js)
    - **MongoDB** (local installation or MongoDB Atlas account)

    ## Installation Steps

    1. **Clone the Repository**
       ```
       git clone https://github.com/yourusername/greentrack.git
       cd greentrack
       ```

    2. **Backend Setup**
       ```
       cd backend
       npm install
       ```

    3. **Frontend Setup**
       ```
       cd ../frontend
       npm install
       ```

    4. **Environment Variables**
       - Create a `.env` file in the `backend` directory with the following content:
         ```
         PORT=5000
         MONGODB_URI=your_mongodb_connection_string
         JWT_SECRET=your_jwt_secret
         ```

    ## Running the Application

    1. **Start the Backend Server**
       ```
       cd backend
       npm start
       ```

    2. **Start the Frontend Development Server**
       ```
       cd ../frontend
       npm start
       ```

    ## Building for Production

    1. **Build Frontend**
       ```
       cd frontend
       npm run build
       ```

    2. **Serve the Build with Backend**
       - Ensure that the backend server is configured to serve static files from the frontend's build directory.
    ]]>
  </setup>
  <files>
    <file>
      <path>backend/package.json</path>
      <content><![CDATA[
{
  "name": "greentrack-backend",
  "version": "1.0.0",
  "description": "Backend for GreenTrack application",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "dev": "nodemon index.js"
  },
  "dependencies": {
    "bcryptjs": "^2.4.3",
    "body-parser": "^1.20.2",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1",
    "express": "^4.18.2",
    "jsonwebtoken": "^9.0.0",
    "mongoose": "^7.3.1"
  },
  "devDependencies": {
    "nodemon": "^2.0.22"
  }
}
      ]]></content>
    </file>
    <file>
      <path>backend/index.js</path>
      <content><![CDATA[
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const bodyParser = require('body-parser');
require('dotenv').config();

// Import Routes
const authRoutes = require('./routes/auth');
const userRoutes = require('./routes/user');

// Initialize Express App
const app = express();

// Middleware
app.use(cors());
app.use(bodyParser.json());

// Routes Middleware
app.use('/api/auth', authRoutes);
app.use('/api/user', userRoutes);

// Connect to MongoDB
mongoose.connect(process.env.MONGODB_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
})
.then(() => console.log('Connected to MongoDB'))
.catch((err) => console.error('MongoDB connection error:', err));

// Start Server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
      ]]></content>
    </file>
    <file>
      <path>backend/models/User.js</path>
      <content><![CDATA[
const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

// Define User Schema
const UserSchema = new mongoose.Schema({
  username: {
    type: String,
    required: true,
    unique: true,
    trim: true,
  },
  email: {
    type: String,
    required: true,
    unique: true,
    lowercase: true,
    trim: true,
  },
  password: {
    type: String,
    required: true,
  },
  carbonData: {
    type: Object,
    default: {},
  },
}, { timestamps: true });

// Password Hashing Middleware
UserSchema.pre('save', async function(next) {
  if (!this.isModified('password')) {
    return next();
  }
  try {
    // Generate salt
    const salt = await bcrypt.genSalt(10);
    // Hash password
    this.password = await bcrypt.hash(this.password, salt);
    next();
  } catch (err) {
    next(err);
  }
});

// Method to Compare Passwords
UserSchema.methods.comparePassword = function(candidatePassword) {
  return bcrypt.compare(candidatePassword, this.password);
};

module.exports = mongoose.model('User', UserSchema);
      ]]></content>
    </file>
    <file>
      <path>backend/routes/auth.js</path>
      <content><![CDATA[
const express = require('express');
const jwt = require('jsonwebtoken');
const User = require('../models/User');

const router = express.Router();

// User Registration Route
router.post('/register', async (req, res) => {
  const { username, email, password } = req.body;

  try {
    // Check if user exists
    let user = await User.findOne({ email });
    if (user) {
      return res.status(400).json({ msg: 'User already exists' });
    }

    // Create new user
    user = new User({
      username,
      email,
      password,
    });

    await user.save();

    // Create JWT Payload
    const payload = {
      user: {
        id: user.id,
      },
    };

    // Sign Token
    jwt.sign(
      payload,
      process.env.JWT_SECRET,
      { expiresIn: '1h' },
      (err, token) => {
        if (err) throw err;
        res.json({ token });
      }
    );

  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server error');
  }
});

// User Login Route
router.post('/login', async (req, res) => {
  const { email, password } = req.body;

  try {
    // Check for user
    let user = await User.findOne({ email });
    if (!user) {
      return res.status(400).json({ msg: 'Invalid Credentials' });
    }

    // Compare Passwords
    const isMatch = await user.comparePassword(password);
    if (!isMatch) {
      return res.status(400).json({ msg: 'Invalid Credentials' });
    }

    // Create JWT Payload
    const payload = {
      user: {
        id: user.id,
      },
    };

    // Sign Token
    jwt.sign(
      payload,
      process.env.JWT_SECRET,
      { expiresIn: '1h' },
      (err, token) => {
        if (err) throw err;
        res.json({ token });
      }
    );

  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server error');
  }
});

module.exports = router;
      ]]></content>
    </file>
    <file>
      <path>backend/routes/user.js</path>
      <content><![CDATA[
const express = require('express');
const jwt = require('jsonwebtoken');
const User = require('../models/User');

const router = express.Router();

// Middleware to Verify Token
const auth = (req, res, next) => {
  // Get token from header
  const token = req.header('Authorization');

  // Check if no token
  if (!token) {
    return res.status(401).json({ msg: 'No token, authorization denied' });
  }

  try {
    // Verify token
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded.user;
    next();
  } catch (err) {
    res.status(401).json({ msg: 'Token is not valid' });
  }
};

// Get User Data
router.get('/me', auth, async (req, res) => {
  try {
    // Fetch user without password
    const user = await User.findById(req.user.id).select('-password');
    res.json(user);
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server error');
  }
});

// Update Carbon Data
router.put('/carbon-data', auth, async (req, res) => {
  const { carbonData } = req.body;

  try {
    let user = await User.findById(req.user.id);
    if (user) {
      user.carbonData = carbonData;
      await user.save();
      return res.json(user);
    } else {
      return res.status(404).json({ msg: 'User not found' });
    }
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server error');
  }
});

module.exports = router;
    ]]></content>
    </file>
    <file>
      <path>frontend/package.json</path>
      <content><![CDATA[
{
  "name": "greentrack-frontend",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "@material-ui/core": "^4.12.4",
    "axios": "^1.4.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.14.1",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  }
}
      ]]></content>
    </file>
    <file>
      <path>frontend/src/index.js</path>
      <content><![CDATA[
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { BrowserRouter } from 'react-router-dom';

// Render the App component wrapped with BrowserRouter for routing
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <BrowserRouter>
    <App />
  </BrowserRouter>
);
      ]]></content>
    </file>
    <file>
      <path>frontend/src/App.js</path>
      <content><![CDATA[
import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './components/Home';
import Register from './components/Register';
import Login from './components/Login';
import Dashboard from './components/Dashboard';

// Main App component with defined routes
function App() {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </>
  );
}

export default App;
      ]]></content>
    </file>
    <file>
      <path>frontend/src/components/Navbar.js</path>
      <content><![CDATA[
import React from 'react';
import { Link } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Button } from '@material-ui/core';

// Navigation bar component
function Navbar() {
  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" style={{ flexGrow: 1 }}>
          GreenTrack
        </Typography>
        <Button color="inherit" component={Link} to="/">Home</Button>
        <Button color="inherit" component={Link} to="/register">Register</Button>
        <Button color="inherit" component={Link} to="/login">Login</Button>
        <Button color="inherit" component={Link} to="/dashboard">Dashboard</Button>
      </Toolbar>
    </AppBar>
  );
}

export default Navbar;
      ]]></content>
    </file>
    <file>
      <path>frontend/src/components/Home.js</path>
      <content><![CDATA[
import React from 'react';
import { Container, Typography } from '@material-ui/core';

// Home page component
function Home() {
  return (
    <Container>
      <Typography variant="h4" gutterBottom>
        Welcome to GreenTrack
      </Typography>
      <Typography variant="body1">
        Monitor and reduce your carbon footprint with actionable insights.
      </Typography>
    </Container>
  );
}

export default Home;
      ]]></content>
    </file>
    <file>
      <path>frontend/src/components/Register.js</path>
      <content><![CDATA[
import React, { useState } from 'react';
import { Container, TextField, Button, Typography } from '@material-ui/core';
import axios from 'axios';

// User registration component
function Register() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
  });

  const { username, email, password } = formData;

  // Handle input changes
  const onChange = e => setFormData({ ...formData, [e.target.name]: e.target.value });

  // Handle form submission
  const onSubmit = async e => {
    e.preventDefault();
    try {
      const res = await axios.post('http://localhost:5000/api/auth/register', formData);
      console.log('Registration successful:', res.data);
      // Redirect or notify user
    } catch (err) {
      console.error('Registration error:', err.response.data);
    }
  };

  return (
    <Container maxWidth="sm">
      <Typography variant="h5" gutterBottom>
        Register
      </Typography>
      <form onSubmit={onSubmit}>
        <TextField
          label="Username"
          name="username"
          value={username}
          onChange={onChange}
          fullWidth
          required
          margin="normal"
        />
        <TextField
          label="Email"
          name="email"
          type="email"
          value={email}
          onChange={onChange}
          fullWidth
          required
          margin="normal"
        />
        <TextField
          label="Password"
          name="password"
          type="password"
          value={password}
          onChange={onChange}
          fullWidth
          required
          margin="normal"
        />
        <Button type="submit" variant="contained" color="primary" fullWidth>
          Register
        </Button>
      </form>
    </Container>
  );
}

export default Register;
      ]]></content>
    </file>
    <file>
      <path>frontend/src/components/Login.js</path>
      <content><![CDATA[
import React, { useState } from 'react';
import { Container, TextField, Button, Typography } from '@material-ui/core';
import axios from 'axios';

// User login component
function Login() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });

  const { email, password } = formData;

  // Handle input changes
  const onChange = e => setFormData({ ...formData, [e.target.name]: e.target.value });

  // Handle form submission
  const onSubmit = async e => {
    e.preventDefault();
    try {
      const res = await axios.post('http://localhost:5000/api/auth/login', formData);
      console.log('Login successful:', res.data);
      // Save token and redirect user
    } catch (err) {
      console.error('Login error:', err.response.data);
    }
  };

  return (
    <Container maxWidth="sm">
      <Typography variant="h5" gutterBottom>
        Login
      </Typography>
      <form onSubmit={onSubmit}>
        <TextField
          label="Email"
          name="email"
          type="email"
          value={email}
          onChange={onChange}
          fullWidth
          required
          margin="normal"
        />
        <TextField
          label="Password"
          name="password"
          type="password"
          value={password}
          onChange={onChange}
          fullWidth
          required
          margin="normal"
        />
        <Button type="submit" variant="contained" color="primary" fullWidth>
          Login
        </Button>
      </form>
    </Container>
  );
}

export default Login;
      ]]></content>
    </file>
    <file>
      <path>frontend/src/components/Dashboard.js</path>
      <content><![CDATA[
import React, { useEffect, useState } from 'react';
import { Container, Typography, Grid, Card, CardContent } from '@material-ui/core';
import axios from 'axios';

// Dashboard component displaying carbon footprint data
function Dashboard() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Fetch user data with token
    const fetchUser = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const res = await axios.get('http://localhost:5000/api/user/me', {
            headers: { 'Authorization': token },
          });
          setUser(res.data);
        } catch (err) {
          console.error('Error fetching user data:', err.response.data);
        }
      }
    };
    fetchUser();
  }, []);

  if (!user) {
    return (
      <Container>
        <Typography variant="h6">Please log in to view your dashboard.</Typography>
      </Container>
    );
  }

  return (
    <Container>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6}>
          <Card>
            <CardContent>
              <Typography variant="h6">Total Carbon Emissions</Typography>
              <Typography variant="h4">{user.carbonData.total || '0'} kg</Typography>
            </CardContent>
          </Card>
        </Grid>
        {/* Additional Cards for Detailed Data */}
      </Grid>
    </Container>
  );
}

export default Dashboard;
      ]]></content>
    </file>
    <file>
      <path>frontend/src/services/authService.js</path>
      <content><![CDATA[
import axios from 'axios';

// Register a new user
export const register = async (userData) => {
  const res = await axios.post('http://localhost:5000/api/auth/register', userData);
  if (res.data.token) {
    localStorage.setItem('token', res.data.token);
  }
  return res.data;
};

// Login user
export const login = async (userData) => {
  const res = await axios.post('http://localhost:5000/api/auth/login', userData);
  if (res.data.token) {
    localStorage.setItem('token', res.data.token);
  }
  return res.data;
};

// Logout user
export const logout = () => {
  localStorage.removeItem('token');
};

// Get current user
export const getCurrentUser = async () => {
  const token = localStorage.getItem('token');
  if (!token) return null;
  const res = await axios.get('http://localhost:5000/api/user/me', {
    headers: { 'Authorization': token },
  });
  return res.data;
};
      ]]></content>
    </file>
    <file>
      <path>frontend/react-scripts</path>
      <content><![CDATA[
<!-- react-scripts content is managed by the create-react-app tool and does not need to be manually edited -->
      ]]></content>
    </file>
    <file>
      <path>backend/.env.example</path>
      <content><![CDATA[
PORT=5000
MONGODB_URI=your_mongodb_connection_string
JWT_SECRET=your_jwt_secret
      ]]></content>
    </file>
    <file>
      <path>frontend/src/App.css</path>
      <content><![CDATA[
/* Basic styling for the GreenTrack app */
body {
  margin: 0;
  font-family: Arial, Helvetica, sans-serif;
}

a {
  text-decoration: none;
  color: inherit;
}
      ]]></content>
    </file>
  </files>
  <run_deploy_steps>
    <![CDATA[
    ## Running the Application Locally

    1. **Start Backend Server**
       ```
       cd backend
       npm run dev
       ```
       This will start the backend server on `http://localhost:5000`.

    2. **Start Frontend Development Server**
       ```
       cd frontend
       npm start
       ```
       This will open the frontend application in your default browser at `http://localhost:3000`.

    ## Deployment Steps

    1. **Build Frontend for Production**
       ```
       cd frontend
       npm run build
       ```
       This creates an optimized production build in the `frontend/build` directory.

    2. **Serve Frontend with Backend**
       - Ensure that the backend server is configured to serve static files from the `frontend/build` directory. You can add the following to `backend/index.js`:
         ```
         const path = require('path');

         // Serve static assets if in production
         if (process.env.NODE_ENV === 'production') {
           app.use(express.static(path.join(__dirname, '../frontend/build')));
           
           app.get('*', (req, res) => {
             res.sendFile(path.resolve(__dirname, '../frontend', 'build', 'index.html'));
           });
         }
         ```
    3. **Choose a Hosting Provider**
       - **Backend:** Heroku, DigitalOcean, or AWS
       - **Frontend:** Netlify, Vercel, or serve via the backend server

    4. **Set Environment Variables**
       - Ensure all necessary environment variables are set on the hosting platform.

    5. **Deploy**
       - Push the code to your chosen hosting provider following their deployment guidelines.

    ## Additional Notes

    - **Database:** Ensure that the MongoDB database is accessible from the deployed backend server.
    - **Security:** Make sure to secure environment variables and enforce HTTPS in production.
    ]]>
  </run_deploy_steps>
  <misc_content>
    <![CDATA[
    <readme>
# GreenTrack

GreenTrack is a web-based application designed to help individuals and small businesses monitor and reduce their carbon footprint. By tracking daily activities, energy consumption, and transportation habits, GreenTrack provides actionable insights and recommendations to promote more sustainable practices.

## Features
- **Carbon Footprint Calculator:** Estimate total carbon emissions based on user input.
- **Personalized Dashboard:** Visualize real-time data on carbon emissions with charts and graphs.
- **Actionable Recommendations:** Receive tailored suggestions to reduce carbon footprint.
- **Goal Setting and Tracking:** Set sustainability goals and monitor progress.
- **Community Engagement:** Participate in forums and community challenges.
- **Integration with Smart Devices:** Connect with smart home devices and fitness trackers.
- **Educational Resources:** Access articles, webinars, and tutorials on sustainability.

## Technology Stack
- **Backend:** Node.js, Express, MongoDB
- **Frontend:** React, Material-UI
- **Authentication:** JWT (JSON Web Tokens)
- **Deployment:** Heroku/DigitalOcean for backend, Netlify/Vercel for frontend

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements.

## License
This project is licensed under the MIT License.
    </readme>
    ]]>
  </misc_content>
  <project_creation_command>
    <![CDATA[
# Commands to Initialize the GreenTrack Project

## Backend
```bash
# Navigate to the desired directory
cd path/to/projects

# Create backend directory
mkdir greentrack && cd greentrack

# Initialize npm and install dependencies
mkdir backend && cd backend
npm init -y
npm install express mongoose dotenv cors body-parser bcryptjs jsonwebtoken
npm install --save-dev nodemon
```

## Frontend
```bash
# Navigate to frontend directory
cd ../
npx create-react-app frontend
cd frontend

# Install additional dependencies
npm install @material-ui/core axios react-router-dom
```

## Final Project Structure
```
greentrack/
├── backend/
│   ├── models/
│   │   └── User.js
│   ├── routes/
│   │   ├── auth.js
│   │   └── user.js
│   ├── .env.example
│   ├── index.js
│   └── package.json
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.js
│   │   │   ├── Home.js
│   │   │   ├── Login.js
│   │   │   ├── Navbar.js
│   │   │   └── Register.js
│   │   ├── services/
│   │   │   └── authService.js
│   │   ├── App.css
│   │   ├── App.js
│   │   └── index.js
│   └── package.json
└── README.md
```
    ]]>
  </project_creation_command>
</developer_output>
"""
    data = parse_developer_xml(xml_str)
    create_project_from_data(data)

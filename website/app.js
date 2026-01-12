// Project data
const projects = {
  ye: {
    title: 'ye',
    cover: 'images/ye.png',
    progress: 42
  },
  carti: {
    title: 'whole lotta red',
    cover: 'images/wholelottared.png',
    progress: 8
  },
  currents: {
    title: 'currents',
    cover: 'images/currents.png',
    progress: 67
  }
};

function showScreen(screenId) {
  document.querySelectorAll('.screen').forEach(screen => {
    screen.classList.remove('active');
  });
  const screen = document.getElementById(screenId);
  if (screen) {
    screen.classList.add('active');
  }
}

// Handle project card clicks - update project detail screen
document.querySelectorAll('.project-card').forEach(card => {
  card.addEventListener('click', function() {
    const projectId = this.getAttribute('data-project');
    if (projectId && projects[projectId]) {
      const project = projects[projectId];
      document.getElementById('project-title').textContent = project.title;
      document.getElementById('album-cover').style.backgroundImage = `url('${project.cover}')`;
      document.getElementById('cover-reveal').style.clipPath = `polygon(0 0, 100% 0, 100% ${100 - project.progress}%, 0 ${100 - project.progress}%)`;
      showScreen('project-detail');
    }
  });
});

// Handle card clicks
document.querySelectorAll('.card[data-screen]').forEach(card => {
  card.addEventListener('click', () => {
    const targetScreen = card.getAttribute('data-screen');
    if (targetScreen) {
      showScreen(targetScreen);
    }
  });
});

// Handle track item clicks
document.querySelectorAll('.track-item[data-screen]').forEach(item => {
  item.addEventListener('click', () => {
    const targetScreen = item.getAttribute('data-screen');
    if (targetScreen) {
      showScreen(targetScreen);
    }
  });
});

// Handle sample card clicks
document.querySelectorAll('.sample-card[data-screen]').forEach(card => {
  card.addEventListener('click', () => {
    const targetScreen = card.getAttribute('data-screen');
    if (targetScreen) {
      showScreen(targetScreen);
    }
  });
});

// Handle pill clicks
document.querySelectorAll('.pill[data-screen]').forEach(pill => {
  pill.addEventListener('click', () => {
    const targetScreen = pill.getAttribute('data-screen');
    if (targetScreen) {
      showScreen(targetScreen);
    }
  });
});

// Handle CTA button clicks
document.querySelectorAll('.cta-button[data-screen]').forEach(button => {
  button.addEventListener('click', () => {
    const targetScreen = button.getAttribute('data-screen');
    if (targetScreen) {
      showScreen(targetScreen);
    }
  });
});

// Assignment functionality
function assignSound(element) {
  const memberName = element.querySelector('h3').textContent;
  element.querySelector('.assign-btn').textContent = 'assigned ✓';
  element.querySelector('.assign-btn').style.background = 'var(--muted)';
  setTimeout(() => {
    showScreen('project-detail');
  }, 500);
}

// Recording timer
let recordingTimer = null;
let recordingSeconds = 0;
const recordBtn = document.getElementById('record-btn');
const timerEl = document.getElementById('timer');

if (recordBtn && timerEl) {
  recordBtn.addEventListener('click', function() {
    if (this.textContent === '●') {
      this.textContent = '⏸';
      this.style.background = '#ff6666';
      recordingSeconds = 0;
      recordingTimer = setInterval(() => {
        recordingSeconds += 0.1;
        timerEl.textContent = recordingSeconds.toFixed(1) + 's';
      }, 100);
    } else {
      this.textContent = '●';
      this.style.background = '#ff4444';
      if (recordingTimer) {
        clearInterval(recordingTimer);
        recordingTimer = null;
      }
      setTimeout(() => {
        showScreen('editing');
      }, 500);
    }
  });
}

// Star rating interaction
document.querySelectorAll('.star').forEach(star => {
  star.addEventListener('click', function() {
    const stars = this.parentElement.querySelectorAll('.star');
    const index = Array.from(stars).indexOf(this);
    stars.forEach((s, i) => {
      if (i <= index) {
        s.classList.add('active');
      } else {
        s.classList.remove('active');
      }
    });
  });
});

// Slider value updates
document.querySelectorAll('.slider').forEach(slider => {
  slider.addEventListener('input', function() {
    const valueSpan = this.parentElement.querySelector('.slider-value');
    if (valueSpan) {
      const value = parseInt(this.value);
      const label = this.parentElement.previousElementSibling?.textContent.toLowerCase() || '';
      
      if (label.includes('tone')) {
        if (value < 25) valueSpan.textContent = 'dark';
        else if (value < 50) valueSpan.textContent = 'warm';
        else if (value < 75) valueSpan.textContent = 'bright';
        else valueSpan.textContent = 'crisp';
      } else if (label.includes('shape')) {
        if (value < 25) valueSpan.textContent = 'soft';
        else if (value < 50) valueSpan.textContent = 'punch';
        else if (value < 75) valueSpan.textContent = 'sharp';
        else valueSpan.textContent = 'hard';
      } else if (label.includes('space') || label.includes('brightness')) {
        if (value < 25) valueSpan.textContent = 'tight';
        else if (value < 50) valueSpan.textContent = 'balanced';
        else if (value < 75) valueSpan.textContent = 'wide';
        else valueSpan.textContent = 'spacious';
      } else if (label.includes('reverb')) {
        if (value < 25) valueSpan.textContent = 'subtle';
        else if (value < 50) valueSpan.textContent = 'moderate';
        else if (value < 75) valueSpan.textContent = 'wet';
        else valueSpan.textContent = 'drenched';
      } else if (label.includes('delay')) {
        if (value < 25) valueSpan.textContent = 'short';
        else if (value < 50) valueSpan.textContent = 'medium';
        else if (value < 75) valueSpan.textContent = 'long';
        else valueSpan.textContent = 'echo';
      } else if (label.includes('compression')) {
        if (value < 25) valueSpan.textContent = 'light';
        else if (value < 50) valueSpan.textContent = 'moderate';
        else if (value < 75) valueSpan.textContent = 'heavy';
        else valueSpan.textContent = 'squashed';
      }
    }
    
    // Handle EQ values
    const eqValue = this.parentElement.querySelector('.eq-value');
    if (eqValue) {
      const value = parseInt(this.value);
      eqValue.textContent = (value >= 0 ? '+' : '') + value + 'db';
    }
  });
});

// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', function() {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active-tab'));
    this.classList.add('active-tab');
  });
});

// Play button animation
document.querySelectorAll('.play-button').forEach(button => {
  button.addEventListener('click', function() {
    this.textContent = this.textContent === '▶︎' ? '⏸' : '▶︎';
    setTimeout(() => {
      if (this.textContent === '⏸') {
        this.textContent = '▶︎';
      }
    }, 2000);
  });
});

// Make pills clickable for filtering (visual feedback)
document.querySelectorAll('.pills .pill').forEach(pill => {
  pill.addEventListener('click', function() {
    this.parentElement.querySelectorAll('.pill').forEach(p => p.classList.remove('active-pill'));
    this.classList.add('active-pill');
  });
});

// Discover card clicks
document.querySelectorAll('.discover-card[data-screen]').forEach(card => {
  card.addEventListener('click', () => {
    const targetScreen = card.getAttribute('data-screen');
    const projectId = card.getAttribute('data-id');
    if (targetScreen) {
      // Update published detail based on which card was clicked
      if (projectId === '1') {
        document.getElementById('published-title').textContent = 'currents';
        document.querySelector('#published-detail .album-cover-large').style.backgroundImage = "url('images/currents.png')";
      } else if (projectId === '2') {
        document.getElementById('published-title').textContent = 'ye';
        document.querySelector('#published-detail .album-cover-large').style.backgroundImage = "url('images/ye.png')";
      } else if (projectId === '3') {
        document.getElementById('published-title').textContent = 'whole lotta red';
        document.querySelector('#published-detail .album-cover-large').style.backgroundImage = "url('images/wholelottared.png')";
      }
      showScreen(targetScreen);
    }
  });
});

// Used in item clicks
document.querySelectorAll('.used-in-item[data-screen]').forEach(item => {
  item.addEventListener('click', () => {
    const targetScreen = item.getAttribute('data-screen');
    if (targetScreen) {
      showScreen(targetScreen);
    }
  });
});

// Borrow sample functionality
function borrowSample(element) {
  const btn = element.querySelector('.borrow-btn');
  btn.textContent = 'borrowed ✓';
  btn.classList.add('borrowed');
  setTimeout(() => {
    showScreen('library');
  }, 500);
}

function borrowAll() {
  document.querySelectorAll('.borrow-btn').forEach(btn => {
    btn.textContent = 'borrowed ✓';
    btn.classList.add('borrowed');
  });
  setTimeout(() => {
    showScreen('library');
  }, 500);
}

function borrowThisSample() {
  setTimeout(() => {
    showScreen('library');
  }, 500);
}

// Publish remake
function publishRemake() {
  setTimeout(() => {
    showScreen('discover');
  }, 500);
}

// Show sample list (placeholder)
function showSampleList() {
  // Could show a modal or scroll to samples section
  document.querySelector('.borrow-list').scrollIntoView({ behavior: 'smooth' });
}

// Show provenance (placeholder)
function showProvenance() {
  // Could show provenance modal or navigate
  showScreen('provenance');
}

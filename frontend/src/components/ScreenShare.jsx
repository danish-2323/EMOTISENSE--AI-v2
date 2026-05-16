import { useState, useEffect, useRef } from 'react'

export default function ScreenShare({ sessionActive, screenStream, setScreenStream, onFocusScore, faceFrame, faceFocus, stress }) {
  const [focusScore, setFocusScore] = useState(null)
  const [lastAlert,  setLastAlert]  = useState(null)
  const [error,      setError]      = useState(null)
  const [offTaskTime, setOffTaskTime] = useState(0)
  const [studyApp,   setStudyApp]   = useState('')  // Which app user will study in
  const [showAppPrompt, setShowAppPrompt] = useState(false)
  const [screenshots, setScreenshots] = useState([])  // Captured distraction/stress screenshots
  const canvasRef   = useRef(null)
  const intervalRef = useRef(null)
  const focusCheckRef = useRef(null)
  const awayStartRef = useRef(null)
  const lastScreenshotRef = useRef(0)  // Prevent duplicate screenshots
  const lastDetectedAppRef = useRef('')  // Track app changes

  const sharing = !!screenStream

  async function startShare() {
    // First, ask which app they'll study in
    setShowAppPrompt(true)
  }

  async function confirmAppAndShare() {
    if (!studyApp.trim()) {
      alert('Please enter the app/website you will be studying in.');
      return;
    }

    setShowAppPrompt(false)

    try {
      const proceed = window.confirm(
        '🖥️ SCREEN SHARING INSTRUCTIONS\n\n' +
        `You said you'll be studying in: "${studyApp}"\n\n` +
        '1. A picker window will open\n' +
        '2. Look for "Entire Screen" tab at the top\n' +
        '3. Select your monitor/screen\n' +
        '4. Click "Share"\n\n' +
        '⚠️ The system will track if you stay in your study app.\n' +
        'You will be alerted if you switch to other apps.\n\n' +
        'Ready to proceed?'
      )
      
      if (!proceed) {
        setShowAppPrompt(true)
        return
      }
      
      const stream = await navigator.mediaDevices.getDisplayMedia({ 
        video: {
          displaySurface: 'monitor',
          width: { ideal: 1920 },
          height: { ideal: 1080 },
          frameRate: { ideal: 30 }
        },
        audio: false,
        preferCurrentTab: false,
        surfaceSwitching: 'exclude',
        selfBrowserSurface: 'exclude',
        systemAudio: 'exclude'
      })
      
      // Verify it's a full screen share
      const track = stream.getVideoTracks()[0]
      const settings = track.getSettings()
      const label = track.label || ''
      
      // Multiple validation checks
      const isScreen = 
        settings.displaySurface === 'monitor' ||
        label.toLowerCase().includes('screen') ||
        label.toLowerCase().includes('monitor') ||
        (settings.width >= 1920 && settings.height >= 1080) // Likely full screen if high res
      
      const isWindow = 
        settings.displaySurface === 'window' ||
        label.toLowerCase().includes('window')
      
      const isTab = 
        settings.displaySurface === 'browser' ||
        label.toLowerCase().includes('tab')
      
      if (isWindow || isTab) {
        track.stop()
        stream.getTracks().forEach(t => t.stop())
        
        const type = isWindow ? 'Window' : 'Chrome Tab'
        setError(
          `❌ WRONG SELECTION: You selected "${type}"\n\n` +
          'This is NOT allowed. You must share your ENTIRE SCREEN.\n\n' +
          'The picker will reopen in 3 seconds.\n\n' +
          'Look for the "Entire Screen" or "Screen" tab at the top of the picker.'
        )
        
        // Auto-retry after 3 seconds
        setTimeout(() => {
          setError(null)
          startShare()
        }, 3000)
        return
      }
      
      if (!isScreen) {
        // Uncertain - show warning but allow
        setError(
          '⚠️ WARNING: Could not verify screen share type.\n\n' +
          'If you selected a Window or Tab, please stop and reshare your ENTIRE SCREEN.'
        )
      }
      
      setScreenStream(stream)
      if (isScreen) setError(null)
      setOffTaskTime(0)
      
      // Listen for user stopping the share
      track.addEventListener('ended', () => {
        setError('⚠️ Screen sharing stopped. Please share your ENTIRE SCREEN again to continue.')
        stopShare()
      })
      
      if ('Notification' in window && Notification.permission === 'default') {
        await Notification.requestPermission()
      }
      
      // Store study app in localStorage for backend
      localStorage.setItem('emotisense_study_app', studyApp)
      
    } catch (err) {
      if (err.name === 'NotAllowedError') {
        setError('❌ Screen share denied. You must share your entire screen to use focus monitoring.')
      } else if (err.name === 'NotFoundError') {
        setError('❌ No screen found. Make sure you have a display connected.')
      } else if (err.name === 'NotSupportedError') {
        setError('❌ Screen sharing not supported in this browser. Please use Chrome, Edge, or Firefox.')
      } else {
        setError(`❌ Screen share failed: ${err.message || 'Unknown error'}`)
      }
    }
  }

  function stopShare() {
    screenStream?.getTracks().forEach(t => t.stop())
    setScreenStream(null)
    clearInterval(intervalRef.current)
    clearInterval(focusCheckRef.current)
  }

  // Monitor browser tab visibility
  useEffect(() => {
    if (!sharing || !sessionActive) return

    function handleVisibilityChange() {
      if (document.hidden) {
        awayStartRef.current = Date.now()
        setLastAlert('⚠️ You switched away from your study screen!')
      } else {
        if (awayStartRef.current) {
          const awayDuration = Math.floor((Date.now() - awayStartRef.current) / 1000)
          setOffTaskTime(prev => prev + awayDuration)
          if (awayDuration > 5) {
            setLastAlert(`You were away for ${awayDuration}s - refocus on your task!`)
          }
          awayStartRef.current = null
        }
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [sharing, sessionActive])

  // Periodic focus check
  useEffect(() => {
    if (!sharing || !sessionActive) return
    focusCheckRef.current = setInterval(() => {
      if (focusScore !== null && focusScore < 40) {
        setLastAlert('🔴 Off-task detected - return to your study material!')
      }
    }, 15000)
    return () => clearInterval(focusCheckRef.current)
  }, [sharing, sessionActive, focusScore])

  // Capture + send every 10 seconds
  useEffect(() => {
    if (!sharing || !sessionActive) return
    intervalRef.current = setInterval(captureAndSend, 10_000)
    captureAndSend()
    return () => clearInterval(intervalRef.current)
  }, [sharing, sessionActive])

  useEffect(() => {
    if (!sessionActive && screenStream) stopShare()
  }, [sessionActive])

  // Helper function to log activities
  function logActivity(activity) {
    const log = JSON.parse(localStorage.getItem('emotisense_activity_log') || '[]')
    log.push(activity)
    localStorage.setItem('emotisense_activity_log', JSON.stringify(log.slice(-200)))  // Keep last 200
  }

  async function captureAndSend() {
    const track = screenStream?.getVideoTracks()[0]
    if (!track) return
    const cap = new ImageCapture(track)
    let blob
    try { blob = await cap.takePhoto() }
    catch { const bmp = await cap.grabFrame(); blob = await bitmapToBlob(bmp) }

    const fd = new FormData()
    fd.append('screenshot', blob, 'screen.jpg')
    fd.append('study_app', studyApp)  // Send the app user should be in
    
    try {
      const res  = await fetch('https://emotisense-e6z2.onrender.com/study/screen', { method: 'POST', body: fd })
      const data = await res.json()
      setFocusScore(data.focus_score)
      setLastAlert(data.alert || null)
      onFocusScore?.(data.focus_score, data.alert)
      
      // Log app change if detected app changed
      const prevApp = lastDetectedAppRef.current
      if (data.detected_app && data.detected_app !== prevApp && prevApp !== '') {
        const isCorrectApp = data.detected_app.toLowerCase().includes(studyApp.toLowerCase())
        logActivity({
          type: 'app-change',
          timestamp: new Date().toISOString(),
          expectedApp: studyApp,
          detectedApp: data.detected_app,
          isCorrectApp,
          focusScore: data.focus_score
        })
        
        // CAPTURE SCREENSHOT ON APP CHANGE (especially if wrong app)
        if (!isCorrectApp) {
          const now = Date.now()
          if (now - lastScreenshotRef.current > 15000) {  // 15 second cooldown for app changes
            lastScreenshotRef.current = now
            await captureDistractedMoment(blob, data, `App changed to ${data.detected_app}`)
          }
        }
      }
      lastDetectedAppRef.current = data.detected_app || 'Unknown'
      
      // Log distraction if focus is low
      if (data.focus_score < 50 || faceFocus < 40) {
        const reason = data.focus_score < 50 && faceFocus < 40 ? 'Wrong app + Face disengaged' :
                       data.focus_score < 50 ? 'Wrong app detected' : 'Face disengaged'
        
        logActivity({
          type: 'distraction',
          timestamp: new Date().toISOString(),
          reason,
          expectedApp: studyApp,
          currentApp: data.detected_app || 'Unknown',
          faceFocus: faceFocus || 0,
          screenFocus: data.focus_score,
          stress: stress || 0
        })
      }
      
      // Capture screenshot if distracted or high stress - MORE AGGRESSIVE
      const now = Date.now()
      const shouldCapture = 
        (data.focus_score < 50 || faceFocus < 40 || stress > 60) &&  // Raised thresholds
        (now - lastScreenshotRef.current > 20000)  // Reduced cooldown to 20 seconds
      
      if (shouldCapture) {
        lastScreenshotRef.current = now
        const trigger = data.focus_score < 50 && faceFocus < 40 ? 'Wrong app + Face disengaged' :
                        data.focus_score < 50 ? `Wrong app: ${data.detected_app}` :
                        faceFocus < 40 ? 'Face disengaged' : 'High stress'
        await captureDistractedMoment(blob, data, trigger)
      }
      
      // If off-task (not in study app), show strong alert
      if (data.focus_score < 50) {  // Raised from 30 to 50
        setLastAlert(`🚨 OFF-TASK: Return to ${studyApp} immediately!`)
        
        if ('Notification' in window && Notification.permission === 'granted') {
          new Notification('EMOTISENSE - Focus Alert', {
            body: data.alert || `You are not in ${studyApp}. Return to your study app now!`,
            requireInteraction: true,
            tag: 'focus-alert'
          })
        }
      } else if (data.focus_score >= 80) {  // Raised from 70 to 80
        setLastAlert(`✅ Excellent! You're focused on ${studyApp}`)
      } else if (data.focus_score >= 60) {
        setLastAlert(`⚠️ Moderate focus - stay on task in ${studyApp}`)
      }
    } catch { /* backend unreachable */ }
  }
  
  async function captureDistractedMoment(screenBlob, analysisData, trigger) {
    try {
      // Capture both screen AND face
      const screenReader = new FileReader()
      
      screenReader.onloadend = () => {
        const screenshot = {
          id: Date.now(),
          timestamp: new Date().toISOString(),
          screenImage: screenReader.result,  // Screen capture
          faceImage: faceFrame ? `data:image/jpeg;base64,${faceFrame}` : null,  // Face capture
          focusScore: analysisData.focus_score,
          faceFocus: faceFocus || 0,
          screenFocus: analysisData.focus_score,
          stressLevel: stress || 0,
          type: analysisData.focus_score < 30 ? 'distraction' : 'stress',
          detectedApp: analysisData.detected_app || 'Unknown',
          reason: analysisData.alert || 'Off-task detected'
        }
        
        setScreenshots(prev => [...prev, screenshot])
        
        // Store in localStorage for report
        const stored = JSON.parse(localStorage.getItem('emotisense_screenshots') || '[]')
        stored.push(screenshot)
        localStorage.setItem('emotisense_screenshots', JSON.stringify(stored.slice(-20)))  // Keep last 20
        
        // Log screenshot capture
        logActivity({
          type: 'screenshot',
          timestamp: screenshot.timestamp,
          trigger,
          detectedApp: analysisData.detected_app || 'Unknown',
          faceFocus: faceFocus || 0,
          screenFocus: analysisData.focus_score,
          stress: stress || 0
        })
      }
      
      screenReader.readAsDataURL(screenBlob)
    } catch (err) {
      console.error('Failed to capture screenshot:', err)
    }
  }

  return (
    <div className="screen-card">
      <div className="screen-header">
        <span className="screen-title">🖥 Screen Focus</span>
        {sharing
          ? <button className="btn-sm btn-danger" onClick={stopShare}>Stop Share</button>
          : <button className="btn-sm btn-primary" onClick={startShare}>Share Screen</button>
        }
      </div>

      {error && <p className="screen-error">{error}</p>}

      {/* App selection prompt */}
      {showAppPrompt && (
        <div className="screen-app-prompt">
          <label className="screen-app-label">
            <span className="screen-app-title">🎯 Which app/website will you study in?</span>
            <input
              type="text"
              className="screen-app-input"
              placeholder="e.g. VS Code, Notion, Google Docs, Khan Academy"
              value={studyApp}
              onChange={e => setStudyApp(e.target.value)}
              autoFocus
            />
            <span className="screen-app-hint">Be specific! This helps track if you stay focused.</span>
          </label>
          <button className="btn-primary" onClick={confirmAppAndShare} style={{ width: '100%', marginTop: 8 }}>
            Continue to Screen Share
          </button>
        </div>
      )}

      {/* Current study app display */}
      {sharing && studyApp && (
        <div className="screen-study-app">
          <span className="screen-study-label">Tracking focus on:</span>
          <span className="screen-study-val">{studyApp}</span>
        </div>
      )}

      {focusScore !== null && (
        <div className="screen-score-row">
          <span className="screen-score-label">Focus Score</span>
          <span className="screen-score-val" style={{ color: focusScore >= 70 ? '#22c55e' : focusScore >= 40 ? '#f59e0b' : '#ef4444' }}>
            {focusScore}
          </span>
        </div>
      )}

      {offTaskTime > 0 && (
        <div className="screen-offtask-time">
          ⏱ Off-task time: {Math.floor(offTaskTime / 60)}m {offTaskTime % 60}s
        </div>
      )}

      {lastAlert && sharing && (
        <div className={`screen-alert ${focusScore >= 70 ? 'screen-alert-success' : focusScore < 30 ? 'screen-alert-danger' : ''}`}>
          {lastAlert}
        </div>
      )}

      {!sharing && !error && (
        <div className="screen-hint-box">
          <div className="screen-requirement">
            <span className="screen-req-icon">🖥️</span>
            <div>
              <p className="screen-hint"><strong>HOW TO SHARE YOUR ENTIRE SCREEN</strong></p>
              
              <div className="screen-steps">
                <div className="screen-step">
                  <span className="step-num">1</span>
                  <span>Click "Share Screen" button below</span>
                </div>
                <div className="screen-step">
                  <span className="step-num">2</span>
                  <span>Look for <strong>"Entire Screen"</strong> tab at the top of the picker</span>
                </div>
                <div className="screen-step">
                  <span className="step-num">3</span>
                  <span>Select your monitor/screen</span>
                </div>
                <div className="screen-step">
                  <span className="step-num">4</span>
                  <span>Click "Share"</span>
                </div>
              </div>
              
              <div className="screen-warning">
                <strong>⚠️ Important:</strong> If you don't see "Entire Screen" tab, it may be hidden on the left side. Look for a monitor/screen icon.
              </div>
              
              <div className="screen-forbidden">
                <strong>❌ DO NOT select:</strong>
                <ul>
                  <li>Window</li>
                  <li>Chrome Tab</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      <canvas ref={canvasRef} style={{ display: 'none' }} />
    </div>
  )
}

async function bitmapToBlob(bmp) {
  const c = document.createElement('canvas')
  c.width = bmp.width; c.height = bmp.height
  c.getContext('2d').drawImage(bmp, 0, 0)
  return new Promise(res => c.toBlob(res, 'image/jpeg', 0.7))
}

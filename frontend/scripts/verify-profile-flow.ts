import {
  authService,
  computeInitials,
  formatNameFromEmail,
  DEFAULT_DEMO_USER,
  DEFAULT_DEMO_SESSION,
  SESSION_STORAGE_KEY,
} from '../services/auth.service'
import type { AccountType, UserProfile, UserSession } from '../types/auth'

// Mock browser localStorage
const mockStorage = new Map<string, string>()
const mockLocalStorage = {
  getItem: (key: string) => mockStorage.get(key) || null,
  setItem: (key: string, value: string) => mockStorage.set(key, String(value)),
  removeItem: (key: string) => mockStorage.delete(key),
  clear: () => mockStorage.clear(),
}

// Assign to global
;(globalThis as any).localStorage = mockLocalStorage
;(globalThis as any).window = globalThis

let totalPassed = 0
let totalTests = 0

function assert(condition: boolean, testName: string, detail?: string) {
  totalTests++
  if (condition) {
    console.log(`[PASS] ${testName}`)
    totalPassed++
  } else {
    console.error(`[FAIL] ${testName}: ${detail || 'Assertion failed'}`)
    process.exitCode = 1
  }
}

console.log('=== CARBONIQ ROLE & ACCOUNT TYPE STATE MANAGEMENT TEST SUITE ===\n')

// TEST 1: Initials & Name Computation
console.log('--- TEST GROUP 1: Initials & Profile Formatting ---')
assert(computeInitials('Aarav Kapoor') === 'AK', 'Initials for "Aarav Kapoor" should be AK')
assert(computeInitials('Priya') === 'PR', 'Initials for single word "Priya" should be PR')
assert(computeInitials('Dr. Sunita Patel') === 'DP', 'Initials for "Dr. Sunita Patel" should be DP')
assert(computeInitials('') === 'CI', 'Empty name defaults to CI')
assert(
  formatNameFromEmail('priya.sharma@domain.com') === 'Priya Sharma',
  'formatNameFromEmail formats dot-separated email'
)
assert(
  formatNameFromEmail('aarav_kapoor@college.edu') === 'Aarav Kapoor',
  'formatNameFromEmail formats underscore-separated email'
)

// TEST 2: Demo Session Creation & Isolation
console.log('\n--- TEST GROUP 2: Demo Session Creation & Isolation ---')
mockLocalStorage.clear()
const demoSession = authService.createDemoSession()
assert(demoSession.mode === 'demo', 'Demo session mode is "demo"')
assert(demoSession.isAuthenticated === false, 'Demo session isAuthenticated is false')
assert(demoSession.user.name === 'Aarav Kapoor', 'Demo user name is "Aarav Kapoor"')
assert(demoSession.user.workspaceName === 'Demo Workspace', 'Demo user workspace is "Demo Workspace"')
assert(demoSession.user.accountType === 'individual', 'Demo user accountType defaults to "individual"')
assert(demoSession.user.id === 'demo-user-aarav', 'Demo user has stable ID "demo-user-aarav"')
assert(demoSession.user.initials === 'AK', 'Demo user initials are "AK"')

// Verify stored in mock storage
const rawStored = mockLocalStorage.getItem(SESSION_STORAGE_KEY)
assert(rawStored !== null, 'Demo session is persisted to storage')
const parsedStored = authService.getStoredSession()
assert(parsedStored?.user.name === 'Aarav Kapoor', 'Stored demo session retrieves correctly')
assert(parsedStored?.user.accountType === 'individual', 'Stored demo user accountType is "individual"')

// TEST 3: Authenticated Mode Creation with Roles (College, Organization, Individual)
console.log('\n--- TEST GROUP 3: Role-Based Account Creation & Persistence ---')
const collegeSession = authService.signUpDemo({
  name: 'Sunita Patel',
  email: 'sunita.patel@iisc.ac.in',
  accountType: 'college',
  workspaceName: 'IISc Campus Operations',
})

assert(collegeSession.mode === 'authenticated', 'College session mode is "authenticated"')
assert(collegeSession.isAuthenticated === true, 'College session isAuthenticated is true')
assert(collegeSession.user.accountType === 'college', 'College accountType is "college"')
assert(collegeSession.user.workspaceName === 'IISc Campus Operations', 'Workspace is preserved')

// Verify stored in storage
const storedCollege = authService.getStoredSession()
assert(storedCollege?.user.accountType === 'college', 'Stored session persists "college" role')

// Organization Role
const orgSession = authService.signUpDemo({
  name: 'Karan Mehra',
  email: 'karan@cleanlogistics.com',
  accountType: 'organization',
  workspaceName: 'Clean Logistics Fleet',
})
assert(orgSession.user.accountType === 'organization', 'Organization accountType is "organization"')
const storedOrg = authService.getStoredSession()
assert(storedOrg?.user.accountType === 'organization', 'Stored session persists "organization" role')

// TEST 4: Backward Compatibility (Legacy Session without accountType defaults to 'individual')
console.log('\n--- TEST GROUP 4: Backward Compatibility Defaults ---')
const legacySessionObj = {
  mode: 'authenticated',
  isAuthenticated: true,
  user: {
    id: 'user-legacy-123',
    name: 'Legacy User',
    email: 'legacy@user.com',
    workspaceName: 'Legacy Workspace',
    // Missing accountType
  },
  createdAt: '2026-01-01T00:00:00.000Z',
}
mockLocalStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(legacySessionObj))
const migratedSession = authService.getStoredSession()
assert(migratedSession?.user.accountType === 'individual', 'Legacy session safely defaults to "individual"')

// TEST 5: Corrupted / Invalid Storage Resilience
console.log('\n--- TEST GROUP 5: Storage Resilience & Recovery ---')
mockLocalStorage.setItem(SESSION_STORAGE_KEY, 'invalid json {!')
const recoveryFromCorrupt = authService.getStoredSession()
assert(recoveryFromCorrupt === null, 'Corrupt JSON safely returns null without throwing')

mockLocalStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify({ mode: 'unknown', foo: 'bar' }))
const recoveryFromInvalid = authService.getStoredSession()
assert(recoveryFromInvalid === null, 'Invalid schema returns null safely')

// TEST 6: Sign-Out Flow
console.log('\n--- TEST GROUP 6: Sign-Out Flow & Cleanup ---')
authService.saveSession(orgSession)
assert(authService.getStoredSession()?.user.name === 'Karan Mehra', 'Session active before sign-out')

// Execute sign out
authService.signOut()
assert(mockLocalStorage.getItem(SESSION_STORAGE_KEY) === null, 'Storage cleared on sign-out')

// Create fresh demo session after sign out
const postSignOutDemo = authService.createDemoSession()
assert(postSignOutDemo.mode === 'demo', 'Post sign-out session is demo mode')
assert(postSignOutDemo.isAuthenticated === false, 'Post sign-out isAuthenticated is false')
assert(postSignOutDemo.user.accountType === 'individual', 'Post sign-out defaults to individual demo')

console.log(`\n========================================`)
console.log(`TEST SUMMARY: ${totalPassed}/${totalTests} tests passed.`)
console.log(`========================================\n`)

if (totalPassed !== totalTests) {
  process.exit(1)
}

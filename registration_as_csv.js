/* STEPS TO USE THIS!
1. Go to duckweb and login.
2. Open the registration portal and click on "View Registration Information".
3. Select the term you want to compile into a CSV.
4. Press F12 to open up the "Devops" code page.
5. Go to the "Network" page at the top, and click on the filter button named: "Fetch/XHR"
6. Reload the page, click on the orange icon link named "getRegistration..."
7. At the top, there should be a little download button that says "export HAR", click it and save it into this folder with a name such as:
    "winter_registration.har"
8. Run the python file :)
*/

// --- Config knobs you can tweak ---
const MAX_DURATION_MINUTES = 119; // skip meetings >= this (likely exams)
const dayNames = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];

// Format times like "4:00 PM"
function formatTime(iso) {
  const d = new Date(iso);
  let h = d.getHours();
  const m = d.getMinutes().toString().padStart(2, "0");
  const ampm = h >= 12 ? "PM" : "AM";
  h = h % 12;
  if (h === 0) h = 12;
  return `${h}:${m} ${ampm}`;
}

// Decide whether to include this meeting in the weekly schedule
function shouldIncludeMeeting(e) {
  const start = new Date(e.start);
  const end = new Date(e.end);
  const durationMinutes = (end - start) / (1000 * 60);

  // Exclude very long blocks (likely exam/final slots)
  if (durationMinutes >= MAX_DURATION_MINUTES) {
    return false;
  }

  return true;
}

// Clean the title so Excel doesn't think it's a formula
function cleanTitle(rawTitle, subject, courseNumber) {
  let t = (rawTitle || "").trim();

  // If it starts with "+", interpret it
  if (t.startsWith("+")) {
    const rest = t.slice(1).trim(); // "Dis", "Lab", etc

    if (/^dis/i.test(rest)) {
      return `${subject} ${courseNumber} Discussion`;
    }
    if (/^lab/i.test(rest)) {
      return `${subject} ${courseNumber} Lab`;
    }

    // Fallback: just drop the plus
    return rest;
  }

  return t;
}

// ---- Group meetings by CRN ----
const byCrn = new Map();

for (const e of events) {
  // Skip meetings we don't want (e.g., long exam periods)
  if (!shouldIncludeMeeting(e)) continue;

  const key = e.crn;

  if (!byCrn.has(key)) {
    byCrn.set(key, {
      term: e.term,
      crn: e.crn,
      subject: e.subject,
      courseNumber: e.courseNumber,
      title: cleanTitle(e.title, e.subject, e.courseNumber),
      meetings: []
    });
  }

  const d = new Date(e.start);
  const day = dayNames[d.getDay()];
  const startTime = formatTime(e.start);
  const endTime = formatTime(e.end);

  const course = byCrn.get(key);

  // avoid duplicates (same day + times)
  if (!course.meetings.some(m => m.day === day && m.start === startTime && m.end === endTime)) {
    course.meetings.push({ day, start: startTime, end: endTime });
  }
}

// ---- Build CSV rows ----
const rows = [["Term","CRN","Subject","Course","Title","Meetings"]];

for (const course of byCrn.values()) {
  const meetingsStr = course.meetings
    .sort((a, b) => {
      const da = dayNames.indexOf(a.day);
      const db = dayNames.indexOf(b.day);
      if (da !== db) return da - db;
      return a.start.localeCompare(b.start);
    })
    .map(m => `${m.day} ${m.start}-${m.end}`)
    .join("; ");

  rows.push([
    course.term,
    course.crn,
    course.subject,
    course.courseNumber,
    course.title,
    meetingsStr
  ]);
}

// ---- Convert to CSV string ----
const csv = rows
  .map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(","))
  .join("\n");

console.log(csv);

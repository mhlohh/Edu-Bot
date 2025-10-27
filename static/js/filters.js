// 🎯 Filter Function
function filterColleges() {
  const search = document.getElementById("search").value.toLowerCase();
  const location = document.getElementById("location-filter").value.toLowerCase();
  const course = document.getElementById("course-filter").value.toLowerCase();
  const maxFee = parseInt(document.getElementById("max-fee").value) || Infinity;

  document.querySelectorAll(".college-card").forEach(card => {
    const name = card.querySelector("h2").textContent.toLowerCase();
    const cardLocation = card.dataset.location.toLowerCase();
    const cardCourses = card.dataset.courses.toLowerCase();
    const cardFee = parseInt(card.dataset.fee);

    const matchesSearch = !search || name.includes(search);
    const matchesLocation = !location || cardLocation.includes(location);
    const matchesCourse = !course || cardCourses.includes(course);
    const matchesFee = cardFee <= maxFee;

    card.style.display = (matchesSearch && matchesLocation && matchesCourse && matchesFee) ? "block" : "none";
  });
}

// 🧠 Event Listeners
document.getElementById("search").addEventListener("input", filterColleges);
document.getElementById("location-filter").addEventListener("change", filterColleges);
document.getElementById("course-filter").addEventListener("change", filterColleges);
document.getElementById("max-fee").addEventListener("input", filterColleges);

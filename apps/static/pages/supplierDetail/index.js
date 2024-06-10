// burger menu
const burgerMenu = document.querySelector('#burgerMenu');
const burgerIcon = document.querySelector('#burgerIcon');
const closeIcon = document.querySelector('#closeIcon');
// search
const searchForm = document.querySelector('#searchForm');
const searchIcon = document.querySelector('#searchIconImg');

const heart = document.querySelector('#heart2');
const heart1 = document.querySelector('#heart1');

const toggleMenu = () => {
  if (burgerMenu.classList.contains('translate-x-0')) {
    burgerMenu.classList.remove('translate-x-0');
    burgerMenu.classList.add('translate-x-full');
  } else {
    burgerMenu.classList.add('translate-x-0');
    burgerMenu.classList.remove('translate-x-full');
  }
};

burgerIcon.addEventListener('click', toggleMenu);
closeIcon.addEventListener('click', toggleMenu);

const toggleFormWidth = () => {
  searchForm.classList.toggle('w-3/4'); // Используйте toggle для переключения класса
  searchForm.classList.toggle('w-min'); // Используйте toggle для переключения класса
};

searchIcon.addEventListener('click', toggleFormWidth);


const toggleActive = () => {
  heart.classList.toggle('text-logo-color');
  heart1.classList.toggle('text-logo-color');
};

heart.addEventListener('click', toggleActive);
heart1.addEventListener('click', toggleActive);
const filterByButtons = document.querySelectorAll('.filterBy');

filterByButtons.forEach(button => {
  button.addEventListener('click', () => {
    filterByButtons.forEach(otherButton => {
      if (otherButton !== button) {
        otherButton.classList.remove('bg-yellow-second');
      }
    });
    button.classList.toggle('bg-yellow-second');
  });
});


// tabs
function openTab(_, tabId) {
  const contents = document.querySelectorAll('.tab-content');
  contents.forEach(content => {
      content.style.display = 'none';
  });

  const allTabs = document.querySelectorAll('.tabs__item');
  allTabs.forEach(tab => {
      tab.classList.remove('active');
  });

  document.getElementById(tabId).style.display = 'block';
  const activeTab = Array.from(allTabs).find(tab => tab.onclick.toString().includes(`'${tabId}'`));
  if (activeTab) {
      activeTab.classList.add('active');
  }
}

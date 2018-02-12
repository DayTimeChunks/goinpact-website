

$(function() {

  // Smooth automatic scrolling (index.html)
  // Source:
  // https://css-tricks.com/smooth-scrolling-accessibility/
  $('a[href*="#"]:not([href="#"])').click(function() {
    if (location.pathname.replace(/^\//,'') == this.pathname.replace(/^\//,'') && location.hostname == this.hostname) {
      var target = $(this.hash);
      target = target.length ? target : $('[name=' + this.hash.slice(1) +']');
      if (target.length) {
        $('html, body').animate({
          scrollTop: target.offset().top
        }, 2000);
        target.focus(); // Setting focus
        if (target.is(":focus")){ // Checking if the target was focused
          return false;
        } else {
          target.attr('tabindex','-1'); // Adding tabindex for elements not focusable
          target.focus(); // Setting focus
        };
        return false;
      }
    }
  });

  // Cookies to determine USER sign in
  var getCookies = function(){
    var pairs = document.cookie.split(";");
    var cookies = {};
    for (var i=0; i<pairs.length; i++){
      var pair = pairs[i].split("=");
      cookies[(pair[0]+'').trim()] = unescape(pair[1]);
    }
    return cookies;
  }
  var cookies = getCookies();
  // console.log("cookie: " , cookies);
  // console.log("cookies.user_id: " , cookies.user_id);
  if (cookies.user_id){
    // console.log("true");
    $('#myinpact-ref').attr("href", "/logout")
    $('#myinpact').text("Log Out")
  } else {
    $('#myinpact-ref').attr("href", "/login")
    $('#myinpact').text("My inPact")
  }

  // $('#new-post').hide()
  if (cookies.admin_id){
    $('#new-post').removeClass('hide-me');
    $('#edit-post').removeClass('hide-me');
    $('#new-post').show()
    $('#edit-post').show()
  } else {
    $('#new-post').hide()
    $('#edit-post').hide()
  }

  /****
  Dynamic text arrangement in onepost.html
  ****/
  var firstImg = $('#img-1');
  firstImg.remove();
  var secondImg = $('#img-2');
  secondImg.remove();
  var thirdImg = $('#img-3');
  thirdImg.remove();
  var textObj = $('#main-text');
  textObj.remove();

  // Convert text and images into arrays
  // to organize the distribution on page
  function isNotEmpty(obj){
    for (var key in obj){
      if (obj.hasOwnProperty(key)){
        return true;
      }
    }
  }

  var array = textObj.text().split("\n");
  // if (isNotEmpty(array)){
  //   console.log("Array is not empty object: " + array.length);
  // } else {
  //   console.log("false");
  // }


  var array_img = [];
  if (isNotEmpty(secondImg)){
    array_img.push(secondImg);
  }
  if (isNotEmpty(thirdImg)){
    array_img.push(thirdImg);
  }

  // console.log(typeof secondImg === 'object');

  // Insert first sentence and first image
  var headline = document.createElement("p");
  var node = document.createTextNode(array[0]);
  // console.log("first node: " + array);
  if (headline !== null && node !== null){
    headline.append(node);
    array.splice(0, 1); // .splice(index, how_many)
    var parent = document.getElementById("main-article");
    if (parent !== null){
      parent.append(headline);
      parent.append(firstImg.get(0));
    }
  }

  // Remove all empty spaces and line breaks in a new array
  var paragraphs = new Array();
  for (var i = 0; i < array.length; i++){
    if (array[i].length > 0){
      paragraphs.push(array[i]);
    }
  }


  // console.log("New array +++++++++" + paragraphs.length);
  // for (var index = 0; index < paragraphs.length; index++){
  //   // console.log("index " + array[i]);
  //   if (paragraphs[index].length > 0){
  //     console.log("p[index] " + paragraphs[index]);
  //     console.log(index);
  //   } else {
  //     console.log("space");
  //   }
  // }
  /**/

  //  Define the number of sections (min = 2)
  // 1 section = 1 text block (of 5 sentences) followed by an image block.
  var sections = 2; // minimum
  var counter = 1;
  for (var p = 0; p < paragraphs.length; p++){
    if (counter === 5){
      sections += 1;
      counter = 0;
    }
  }
  // console.log("Sections: " + sections);
  var p_counter = 1;
  // console.log("ini_paragraphs.length: " + ini_paragraphs.length);
  var tot_paragraphs = paragraphs.length;
  while (paragraphs.length > 0){
    p_counter += 1;
    var new_p = document.createElement("p");
    node = document.createTextNode(paragraphs[0]);
    // console.log("node:" + array[0]==="");
    // console.log("node:" + array[0].length);
    new_p.append(node);
    parent.append(new_p);
    paragraphs.splice(0, 1); // delte first paragraph
    if (p_counter === sections){
      // Append 2nd or 3rd image to DOM
      if (array_img.length > 1){
        parent.append(array_img[0].get(0));
        array_img.splice(0,1);
        p_counter = 0;
      } else {
        p_counter = 0;
        continue;
      }
    }
  }
  //  Finally include remaining images
  while (array_img.length > 0){
    parent.append(array_img[0].get(0));
    array_img.splice(0,1);
  }




  // $(document).ready(function(){
  //     $('[data-toggle="tooltip"]').tooltip();
  // });

  // Sign-up | Sign-in page
  // Initialisieren, ohne Objekt möglich
  // TabPages.init('myTabPage');
  //
  // // Um eine Page vor zu selektieren, braucht man das Objekt aber
  // var tab = TabPages.init('myTabPage');
  // tab.selectTab('page3');

  // geht auch klassich
  // var myTabElement = new TabPages('myTabPage');
  // myTabElement.initTabs();
  // myTabElement.selectTab('page3');


});

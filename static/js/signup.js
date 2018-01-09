



// $(function () {
//
//     $('#sign-in-tab a:first').tab('show')
//     $('#sign-in-tab a').click(function (e) {
//       e.preventDefault()
//       $(this).tab('show')
//     })
//
//     $('#sign-up-tab a').click(function (e) {
//       e.preventDefault()
//       $(this).tab('show')
//     })
//     //
//
//
//     // Javascript to enable link to tab
//     var url = document.location.toString();
//     console.log("url: ", url);
//     if (url.match('#')) {
//       console.log("match: ", url.match('#') );
//       $('.nav-tabs a[href="#' + url.split('#')[1] + '"]').tab('show');
//     }
//
//     // Change hash for page-reload
//     $('.nav-tabs a').on('show.bs.tab', function (e) {
//         window.location.hash = e.target.hash;
//
//     })
//
// })


$(function () {

  // TODO:
  // Need to authenticate user, and store it in the database
  // https://developers.google.com/identity/sign-in/web/sign-in
  // https://developers.google.com/identity/sign-in/web/backend-auth

  // Google-sign in
  function onSignIn(googleUser) {
    var profile = googleUser.getBasicProfile();
    console.log('ID: ' + profile.getId()); // Do not send to your backend! Use an ID token instead.
    console.log('Name: ' + profile.getName());
    console.log('Image URL: ' + profile.getImageUrl());
    console.log('Email: ' + profile.getEmail()); // This is null if the 'email' scope is not present.


    // var id_token = googleUser.getAuthResponse().id_token;
    // var xhr = new XMLHttpRequest();
    // xhr.open('POST', 'https://yourbackend.example.com/tokensignin');
    // xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    // xhr.onload = function() {
    //   console.log('Signed in as: ' + xhr.responseText);
    // };
    // xhr.send('idtoken=' + id_token);
  }

  // var hash = window.location.hash;
  // console.log("hash: " , hash);
  // if (hash){
  //   console.log("hash2: " , hash);
  // }


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
  console.log("cookie: " , cookies);

  console.log("cookies.user_id: " , cookies.user_id);
  if (cookies.user_id){
    console.log("true");
    $('#myinpact-ref').attr("href", "/logout")
    $('#myinpact').text("Log Out")
    // $('#signup-dd').addClass(" d-none ")
    // $('#login-dd').addClass(" d-none ")
    // $('#logout-dd').removeClass(" d-none ")
  } else {
    $('#myinpact-ref').attr("href", "/login")
    $('#myinpact').text("My inPact")

    // $('#signup-dd').removeClass(" d-none ")
    // $('#login-dd').removeClass(" d-none ")
    // $('#logout-dd').addClass(" d-none ")
  }

})

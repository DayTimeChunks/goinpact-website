



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

function onSignIn(googleUser){
  var profile = googleUser.getBasicProfile();
  if (profile){
    console.log('JS google ID: ' + profile.getId()); // Do not send to your backend! Use an ID
    var id_token = googleUser.getAuthResponse().id_token;
    console.log('idtoken is: ' + id_token);
    var xhr = new XMLHttpRequest();
    // Identify the document to open (i.e. the URL)
    // var url = 'http://localhost:8080/tokensignin';
    var url = 'http://localhost:8080/tokensignin';
    xhr.open('POST', url); // '/tokensignin' doesn't exist yet, but not sure what it should do or contain since the only thing I want is a place to store the token in the backend (i.e. to be able to retrieve it)

    // To POST data like an HTML form, add an HTTP header with setRequestHeader().
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.onload = function() {
      // Response will be the URL declared in 'POST'
      console.log('Signed in as: ' + xhr.responseText);
      // window.location.replace("/glogin")
    };
    // Specify the data you want to send in the send() method:
    xhr.send('idtoken=' + id_token); // RESULT: I cannot see a new header item with key 'idtoken' when I do check fo headers via 'urllib2.urlopen(url).headers.items()' on main.py

    // TODO: replace this cookie method with
    // a GET request from main.py
    // document.cookie = "idtoken=" + id_token;


  } else {
    console.log("Profile is undefined");
  }
  //console.log('ID: ' + profile.getId()); // Do not send to your backend! Use an ID token instead.
  //console.log('Image URL: ' + profile.getImageUrl());
  //console.log('Name: ' + profile.getName());
  //console.log('Email: ' + profile.getEmail());
  // var user_uname = profile.getName();
  // var user_email = profile.getEmail();
  // alert(user_uname);
  // var attempt = 0;
  // if (attempt == 0){
  //   // window.location.href= window.location.href
  //   // Redirect is working, now
  //   // Redirect to my inPact page - handle in main.py,
  //   // and activate googleyolo.retrieve where
  //   // "continue as Pablo" will be asked, then POST token
  //   // get token on backend and verify User, then Load myInpact Page Content
  //   window.location.replace("/blog")
  //   attempt +=1;
  // }

}


// window.onGoogleYoloLoad = (googleyolo) => {
//   const retrievePromise = googleyolo.retrieve({
//     supportedAuthMethods: [
//       "https://accounts.google.com",
//       "googleyolo://id-and-password"
//     ],
//     supportedIdTokenProviders: [
//       {
//         uri: "https://accounts.google.com",
//         clientId: "902461304999-hgej779q0upelr8ejpoeqfj5k0tppm2k.apps.googleusercontent.com"
//       }
//     ]
//   });
//
//   console.log("retrivePromise " + retrievePromise);
//
//   retrievePromise.then((credential) => {
//     if (credential.password) {
//       // An ID (usually email address) and password credential was retrieved.
//       // Sign in to your backend using the password.
//       signInWithEmailAndPassword(credential.id, credential.password);
//     } else {
//       // A Google Account is retrieved. Since Google supports ID token responses,
//       // you can use the token to sign in instead of initiating the Google sign-in
//       // flow.
//       useGoogleIdTokenForAuth(credential.idToken);
//     }
//   }, (error) => {
//     // Credentials could not be retrieved. In general, if the user does not
//     // need to be signed in to use the page, you can just fail silently; or,
//     // you can also examine the error object to handle specific error cases.
//
//     console.log("Error type: " + error.type);
//
//     // If retrieval failed because there were no credentials available, and
//     // signing in might be useful or is required to proceed from this page,
//     // you can call `hint()` to prompt the user to select an account to sign
//     // in or sign up with.
//     if (error.type === 'noCredentialsAvailable') {
//       // googleyolo.hint(...).then(...);
//       const hintPromise = googleyolo.hint({
//         supportedAuthMethods: [
//           "https://accounts.google.com"
//         ],
//         supportedIdTokenProviders: [
//           {
//             uri: "https://accounts.google.com",
//             clientId: "902461304999-hgej779q0upelr8ejpoeqfj5k0tppm2k.apps.googleusercontent.com"
//           }
//         ]
//       });
//
//       console.log("hintPromise" + hintPromise);
//
//       hintPromise.then((credential) => {
//         if (credential.idToken) {
//           // Send the token to your auth backend.
//           console.log("credential.idToken: " + credential.idToken);
//           useGoogleIdTokenForAuth(credential.idToken);
//         }
//       }, (error) => {
//         switch (error.type) {
//           case "userCanceled":
//             // The user closed the hint selector. Depending on the desired UX,
//             // request manual sign up or do nothing.
//             break;
//           case "noCredentialsAvailable":
//             // No hint available for the session. Depending on the desired UX,
//             // request manual sign up or do nothing.
//             break;
//           case "requestFailed":
//             // The request failed, most likely because of a timeout.
//             // You can retry another time if necessary.
//             break;
//           case "operationCanceled":
//             // The operation was programmatically canceled, do nothing.
//             break;
//           case "illegalConcurrentRequest":
//             // Another operation is pending, this one was aborted.
//             break;
//           case "initializationError":
//             // Failed to initialize. Refer to error.message for debugging.
//             break;
//           case "configurationError":
//             // Configuration error. Refer to error.message for debugging.
//             break;
//           default:
//             // Unknown error, do nothing.
//         }
//       });
//
//
//     }
//   });
//
// }




// window.onGoogleYoloLoad = (googleyolo) => {
//   googleyolo.hint({
//     supportedAuthMethods: [
//       "https://accounts.google.com"
//     ],
//     supportedIdTokenProviders: [{
//       uri: "https://accounts.google.com",
//       clientId: "902461304999-hgej779q0upelr8ejpoeqfj5k0tppm2k.apps.googleusercontent.com"
//     }],
//     context: "signUp"
//   }).then((credential) => {
//     console.log("credential: " + credential);
//   }, (error) => {
//     console.log(error.type);
//   });
// };

//  TODO: If Sign-Up button is clicked,
// googleyolo.cancelLastOperation().then(() => {
//   // Credential selector closed.
// });

// $(function () {
//
//
//
//
//
//   // TODO:
//   // Need to authenticate user, and store it in the database
//   // https://developers.google.com/identity/sign-in/web/sign-in
//   // https://developers.google.com/identity/sign-in/web/backend-auth
//
//
//
//
//
// })

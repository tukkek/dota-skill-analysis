// ==UserScript==
// @name         Dotabuff match ID extractor
// @namespace    tukkek
// @version      1.0
// @description  Easiy get match IDs from Dotabuff
// @author       Alex Henry
// @match        https://www.dotabuff.com/matches?*
// @grant        none
// ==/UserScript==

const TOKEN='matches/';

window.addEventListener('load',function(){
    let ids=Array.from(document.querySelectorAll('a'))
        .filter(l=>l.href.indexOf(TOKEN)>0)
        .map(l=>l.href.substring(l.href.indexOf(TOKEN)+TOKEN.length,l.href.length));
    if(ids.length>0) console.log('Match IDs: '+ids.join(' '));
});
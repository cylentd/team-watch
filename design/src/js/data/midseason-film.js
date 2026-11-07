function msFilmMoment(time){
  const scene = time < MS_FILM.standingsEnd ? 0 : time < MS_FILM.raceEnd ? 1 : 2;
  return {scene, time: Math.max(0, Math.min(MS_FILM.duration, time))};
}

function msFilmTime(time){
  return "0:" + String(Math.floor(time / MS_FILM.second)).padStart(2, "0");
}

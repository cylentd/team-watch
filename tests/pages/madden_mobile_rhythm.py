from pages.madden_lineups_set import LineupsSetFilm


class MobileRhythmFilm(LineupsSetFilm):
    def manager_geometry(self):
        return self.page.evaluate("""() => {
          const section=document.querySelector('[data-lineup-headline]');
          const manager=section.querySelector('[data-defense-manager]');
          const image=manager.querySelector('img'), name=manager.querySelector('span');
          const title=section.querySelector('[data-lineup-outcome]');
          const rect=node=>{const b=node.getBoundingClientRect();return {top:b.top,bottom:b.bottom,left:b.left,right:b.right,width:b.width,height:b.height};};
          return {avatar:rect(image), nameSize:parseFloat(getComputedStyle(name).fontSize), titleSize:parseFloat(getComputedStyle(title).fontSize), header:rect(section)};
        }""")

import { LitElement, html, css } from 'lit-element'
import { connect } from 'pwa-helpers'
import { store } from '../store.js'

import '@material/mwc-icon'
import '@polymer/paper-ripple'

class SidenavMenu extends connect(store)(LitElement) {
  static get properties() {
    return {
      config: { type: Object },
      urls: { type: Object }
    }
  }

  static get styles() {
    return [
      css`
        .mcd-menu {
          list-style: none;
          padding: 0;
          margin: 0;
          background: #FFF;
          border-radius: 2px;
          -moz-border-radius: 2px;
          -webkit-border-radius: 2px;
          width: 100%;
          outline: none;
          background-color: #b5f7f4;
        }
        .mcd-menu li {
          position: relative;
          /* height:48px; */
          line-height: 48px;
          outline: none;
          padding: 2px;
          list-style: none;
        }
        .mcd-menu li a {
          display: block;
          text-decoration: none;
          padding-left: 20px;
          color: var(--mdc-theme-on-surface);
          text-align: left;
          height: 48px;
          position: relative;
          border-bottom: 1px solid #EEE;
          outline: none;
        }
        .mcd-menu li a mwc-icon {  
          float: left;
          margin: 0 10px 0 0;
          padding-top: 14px;
          padding-right: 9px;
        }

        .mcd-menu li a span {
          display: block;
          text-transform: uppercase;
          outline: none;
        }

        .mcd-menu li a small {
          display: block;
          font-size: 10px;
          outline: none;
        }

        .mcd-menu li:hover > a mwc-icon {
            opacity: 1;
        }
        .mcd-menu li:hover a span {
            opacity: 1;
            outline: none;
        }

        .mcd-menu li:hover > a {
            background: #f8f8f8;
            color: #515151;
        }
        .mcd-menu li a.active {
          position: relative;
          color: #515151;
          background-color: #eee;
          outline: none;
        }
        .mcd-menu li a.active:before {
          content: "";
          position: absolute;
          top: 42%;
          left: 0;
          border-left: 5px solid #515151;
          border-top: 5px solid transparent;
          border-bottom: 5px solid transparent;
          outline: none;
        }

        .mcd-menu li a.active:after {
          content: "";
          position: absolute;
          top: 42%;
          right: 0;
          border-right: 5px solid #515151;
          border-top: 5px solid transparent;
          border-bottom: 5px solid transparent;
          outline: none;
        }

        .mcd-menu li ul,
        .mcd-menu li ul li ul {
          position: absolute;
          height: auto;
          min-width: 240px;
          padding: 0;
          margin: 0;
          background: #FFF;
          opacity: 0;
          visibility: hidden;
          transition: all 300ms linear;
          -o-transition: all 300ms linear;
          -ms-transition: all 300ms linear;
          -moz-transition: all 300ms linear;
          -webkit-transition: all 300ms linear;
          z-index: 999999999;
          right:280px;
          top: 0px;
          border-right: 4px solid #515151;
          outline: none;
        }
        .mcd-menu li ul:before {
          content: "";
          position: absolute;
          top: 25px;
          right: -9px;
          border-left: 5px solid #515151;
          border-bottom: 5px solid transparent;
          border-top: 5px solid transparent;
          outline: none;
        }
        .mcd-menu li:hover > ul,
        .mcd-menu li ul li:hover > ul {
          display: block;
          opacity: 1;
          visibility: visible;
          right: 280px;
          outline: none;
        }

        .mcd-menu li ul li a {
          /* padding: 10px; */
          text-align: left;
          border: 0;
          border-bottom: 1px solid #EEE;
          height: auto;
          outline: none;
        }
        .mcd-menu li ul li a mwc-icon {
          /* font-size: 16px; */
          display: inline-block;
          margin: 0 10px 0 0;
        }
        .mcd-menu li ul li ul {
          left: 230px;
          top: 0;
          border: 0;
          border-left: 4px solid #515151;
          outline: none;
        }  
        .mcd-menu li ul li ul:before {
          content: "";
          position: absolute;
          top: 15px;
          right: -9px;
          border-left: 5px solid #515151;
          border-bottom: 5px solid transparent;
          border-top: 5px solid transparent;
          outline: none;
        }
        .mcd-menu li ul li:hover > ul {
          top: 0px;
          left: 200px;
          outline: none;
        }
      `
    ]
  }

  constructor() {
    super()
    this.urls = []
  }

  render() {
    return html`
            <style>

            </style>
            
            <div>
                <ul class="mcd-menu">
                    ${this.urls.map(myPlugin => myPlugin.menus.length === 0 ? html`
                        <li>
                            <paper-ripple></paper-ripple>
                            <a href="/app/${myPlugin.url}">
                                <mwc-icon>${myPlugin.icon}</mwc-icon>
                                <span>${myPlugin.title}</span>
                            </a>
                        </li>
                    ` : html`
                        <li>
                            <paper-ripple></paper-ripple>
                            <a href="/app/${myPlugin.url}">
                                <mwc-icon>${myPlugin.icon}</mwc-icon>
                                <span>${myPlugin.title}</span>
                            </a>
                            
                            <ul>
                                ${myPlugin.menus.map(myMenu => html`
                                    <li>
                                        <paper-ripple></paper-ripple>
                                        <a href="/app/${myMenu.url}">
                                            <mwc-icon>${myMenu.icon}</mwc-icon>
                                            <span>${myMenu.title}</span>
                                        </a>
                                    </li>
                                `)}
                            </ul>
                        </li>
                    `)}
                </ul>
            </div>
        `
  }

  firstUpdated() {
    // ...
  }

  stateChanged(state) {
    this.config = state.config
    this.urls = state.app.registeredUrls
  }
}

window.customElements.define('sidenav-menu', SidenavMenu)

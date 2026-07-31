import { LitElement, html, css } from 'lit-element'
import { connect } from 'pwa-helpers'
import { store } from '../store.js'

import '@polymer/paper-icon-button/paper-icon-button.js'
import '@polymer/iron-icons/iron-icons.js'

import './wallet-profile.js'
import './app-info.js'
import './sidenav-menu.js'
import './show-plugin.js'

import '@material/mwc-drawer'

import '@polymer/app-layout/app-layout.js'
import '@polymer/paper-ripple'

import './settings-view/user-settings.js'

class AppView extends connect(store)(LitElement) {
    static get properties() {
        return {
            config: { type: Object }
        }
    }

    static get styles() {
        return [
            css`
            :host {
                --app-drawer-width: 260px;
            }

            app-drawer-layout:not([narrow]) [drawer-toggle]:not(sidenav-menu) {
                display: none;
            }

            app-drawer {
                box-shadow: var(--shadow-2);
                background: var(--mdc-theme-surface);
            }
            app-header {
                box-shadow: var(--shadow-2);
            }
            app-toolbar {
                background: #b5f7f4;
                color: var(--mdc-theme-on-surface);
            }

            #sideBar {
                background-color: #b5f7f4;
                height: 100vh;
                display: flex;
                flex: 1 1;
                flex-direction: column;
                justify-content: space-between;
            }

            #sideBar::-webkit-scrollbar {
                width: 7px;
                background-color: transparent;
            }

            #sideBar::-webkit-scrollbar-track {
                background-color: transparent;
            }

            #sideBar::-webkit-scrollbar-thumb {
                background-color: #333;
                border-radius: 6px;
                border: 3px solid #333;
            }
        `
        ]
    }

    render() {
        return html`
        <style>

        </style>
        <app-drawer-layout responsive-width='${getComputedStyle(document.body).getPropertyValue('--layout-breakpoint-desktop')}' fullbleed >
            <app-drawer swipe-open slot="drawer" id="appdrawer" style="position: absolute; right: 0; left: auto;">
                <app-header-layout>
                    <div id="sideBar">
                        <div>
                            <wallet-profile></wallet-profile>

                            <sidenav-menu></sidenav-menu>
                        </div>

                        <div>
                            <app-info></app-info>
                        </div>
                    </div>
                </app-header-layout>
            </app-drawer>

            <app-header-layout style="height: var(--window-height); left: -260px; right: 260px;">

                <app-header id='appHeader' slot="header" style="left: 0px; right:260px;" fixed>
                    <app-toolbar>

                        <paper-icon-button class="menu-toggle-button" drawer-toggle icon="menu"></paper-icon-button>

                        <div main-title>
                            <span class="qora-title">
                                <img src="${this.config.coin.logo}" style="height:55px; padding-left:12px;">
                            </span>
                        </div>

                        <div style="display:inline">
                            <paper-icon-button icon="icons:settings" @click=${ () => this.openSettings()} title="Settings" ></paper-icon-button>
                        </div>
                    </app-toolbar>
                </app-header>

                <show-plugin></show-plugin>
                    
            </app-header-layout>
        </app-drawer-layout>
        <user-settings></user-settings>
    `
    }

    constructor() {
        super()

    }

    firstUpdated() {
        //
    }

    stateChanged(state) {
        this.config = state.config
    }

    openSettings() {

        const settingsDialog = document.getElementById('main-app').shadowRoot.querySelector('app-view').shadowRoot.querySelector('user-settings')
        settingsDialog.openSettings()
    }
}

window.customElements.define('app-view', AppView)

//
//  global.mutations.ts
//  InspiringApps modules
//
//  Created by InspiringApps on 4/12/20.
//  Copyright © 2024. InspiringApps. All rights reserved.
//

import { AppMessage } from '@/models/AppMessage/AppMessage.model';
import { State } from './global.state';

export enum MutationTypes {
    BEGIN_LOADING = '[Global] Begin loading',
    END_LOADING = '[Global] End loading',
    SET_ERROR = '[Global] Error set',
    PUSH_MESSAGE = '[Global] Message push',
    CLEAR_MESSAGES = '[Global] Messages clear',
    STORE_UPDATE_SEARCH = '[Global] Update search term',
    STORE_RESET_GLOBAL = '[Global] Store reset',
    SET_MODAL_OPEN = '[Global] Modal isOpen set',
    SET_MODAL_LOGOUT_ONLY = '[Global] Modal isLogoutOnly set',
}

export default {
    [MutationTypes.BEGIN_LOADING]: (state: State) => {
        state.isLoading = true;
        state.error = null;
    },
    [MutationTypes.END_LOADING]: (state: State) => {
        state.isLoading = false;
    },
    [MutationTypes.SET_ERROR]: (state: State, error: object | string) => {
        state.error = error || null;
    },
    [MutationTypes.PUSH_MESSAGE]: (state: State, message: AppMessage) => {
        state.messages = (state.messages) ? state.messages.concat(message) : [message];
    },
    [MutationTypes.CLEAR_MESSAGES]: (state: State) => {
        state.messages = [];
    },
    [MutationTypes.SET_MODAL_OPEN]: (state: State, isOpen: boolean) => {
        state.isModalOpen = isOpen;
    },
    [MutationTypes.SET_MODAL_LOGOUT_ONLY]: (state: State, isLogoutOnly: boolean) => {
        state.isModalLogoutOnly = isLogoutOnly;
    },
    [MutationTypes.STORE_RESET_GLOBAL]: (state: any) => {
        state.isLoading = false;
        state.error = null;
        state.messages = [];
        state.isModalOpen = false;
        state.isModalLogoutOnly = false;
    },
};

<!--
    LicenseeList.vue
    CompactConnect

    Created by InspiringApps on 7/1/2024.
-->

<template>
    <div class="licensee-list-container">
        <h1 class="list-title">{{ $t('licensing.licensingListTitle') }}</h1>
        <ListContainer
            :listId="listId"
            :listData="this.licenseStore.model"
            :listSize="this.licenseStore.total"
            :sortOptions="sortOptions"
            :sortChange="sortingChange"
            :pageChange="paginationChange"
            :excludeSorting="false"
            :excludeTopPagination="true"
            :excludeBottomPagination="false"
            :isServerPaging="true"
            :isLoading="$store.state.license.isLoading"
            :loadingError="$store.state.license.error"
        >
            <template v-slot:headers>
                <LicenseeRow
                    :listId="listId"
                    :item="headerRecord"
                    :isHeaderRow="true"
                    :sortOptions="sortOptions"
                    :sortChange="sortingChange"
                />
            </template>
            <template v-slot:list>
                <LicenseeRow
                    v-for="(record, index) in this.licenseStore.model"
                    :key="index"
                    :listId="listId"
                    :item="record"
                />
            </template>
        </ListContainer>
    </div>
</template>

<script lang="ts" src="./LicenseeList.ts"></script>
<style scoped lang="less" src="./LicenseeList.less"></style>
